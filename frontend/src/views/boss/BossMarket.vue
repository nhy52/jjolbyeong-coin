<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  marketApi,
  type Order,
  type Product,
  type ProductInput,
  type ProductRequest,
} from '@/api/market'
import { useMarketStream } from '@/composables/useMarketStream'
import { ApiError } from '@/lib/http'

const products = ref<Product[]>([])
const orders = ref<Order[]>([])
const requests = ref<ProductRequest[]>([])
const loading = ref(true)
const busyOrderId = ref<number | null>(null)
const busyReqId = ref<number | null>(null)

const tab = ref<'products' | 'orders' | 'requests'>('products')
const pendingOrders = computed(() => orders.value.filter((o) => o.status === 'purchased'))
const pendingRequests = computed(() => requests.value.filter((r) => r.status === 'pending'))

// 거절 사유 시트
const rejecting = ref<ProductRequest | null>(null)
const rejectReason = ref('')

// 상품 등록/수정 시트
const editing = ref<Product | null>(null) // null = 신규
const showForm = ref(false)
const form = ref<{ name: string; price_coin: number; description: string; stock: string; image_url: string | null }>({
  name: '',
  price_coin: 100,
  description: '',
  stock: '',
  image_url: null,
})
const uploading = ref(false)
const saving = ref(false)
const formError = ref('')

async function load() {
  loading.value = true
  try {
    const [ps, os, rs] = await Promise.all([
      marketApi.products(),
      marketApi.orders(),
      marketApi.requests(),
    ])
    products.value = ps
    orders.value = os
    requests.value = rs
  } finally {
    loading.value = false
  }
}

function upsertRequest(r: ProductRequest) {
  const i = requests.value.findIndex((x) => x.id === r.id)
  if (i >= 0) requests.value[i] = r
  else requests.value.unshift(r)
}

const { connect } = useMarketStream({
  onOrderCreated: (o) => {
    orders.value.unshift(o)
  },
  onRequestCreated: upsertRequest,
  onRequestUpdated: upsertRequest,
})

function openNew() {
  editing.value = null
  form.value = { name: '', price_coin: 100, description: '', stock: '', image_url: null }
  formError.value = ''
  showForm.value = true
}
function openEdit(p: Product) {
  editing.value = p
  form.value = {
    name: p.name,
    price_coin: p.price_coin,
    description: p.description ?? '',
    stock: p.stock === null ? '' : String(p.stock),
    image_url: p.image_url,
  }
  formError.value = ''
  showForm.value = true
}
function closeForm() {
  showForm.value = false
}

async function onFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = true
  formError.value = ''
  try {
    const { image_url } = await marketApi.uploadImage(file)
    form.value.image_url = image_url
  } catch (err) {
    formError.value = err instanceof Error ? err.message : '이미지 업로드에 실패했어요.'
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function save() {
  if (!form.value.name.trim() || form.value.price_coin <= 0) {
    formError.value = '이름과 가격(1 이상)을 입력해 주세요.'
    return
  }
  saving.value = true
  formError.value = ''
  const payload: ProductInput = {
    name: form.value.name.trim(),
    price_coin: form.value.price_coin,
    description: form.value.description.trim() || null,
    image_url: form.value.image_url,
    stock: form.value.stock.trim() === '' ? null : Math.max(0, Number(form.value.stock)),
  }
  try {
    if (editing.value) {
      const updated = await marketApi.updateProduct(editing.value.id, payload)
      const i = products.value.findIndex((x) => x.id === updated.id)
      if (i >= 0) products.value[i] = updated
    } else {
      const created = await marketApi.createProduct(payload)
      products.value.unshift(created)
    }
    closeForm()
  } catch (e) {
    formError.value = e instanceof ApiError ? e.message : '저장에 실패했어요.'
  } finally {
    saving.value = false
  }
}

async function removeProduct(p: Product) {
  if (!confirm(`'${p.name}' 상품을 삭제할까요?`)) return
  await marketApi.deleteProduct(p.id)
  // 주문이 있으면 서버가 hidden 처리 → 재조회로 상태 동기화
  await load()
}

async function toggleHidden(p: Product) {
  const next = p.status === 'hidden' ? 'on_sale' : 'hidden'
  const updated = await marketApi.updateProduct(p.id, { status: next })
  const i = products.value.findIndex((x) => x.id === updated.id)
  if (i >= 0) products.value[i] = updated
}

async function fulfill(o: Order) {
  busyOrderId.value = o.id
  try {
    const updated = await marketApi.fulfill(o.id)
    const i = orders.value.findIndex((x) => x.id === o.id)
    if (i >= 0) orders.value[i] = updated
  } finally {
    busyOrderId.value = null
  }
}

async function approveRequest(r: ProductRequest) {
  busyReqId.value = r.id
  try {
    const updated = await marketApi.approveRequest(r.id)
    upsertRequest(updated)
    // 승인 시 생성된 상품을 상품 목록에도 반영
    const ps = await marketApi.products()
    products.value = ps
  } catch (e) {
    alert(e instanceof ApiError ? e.message : '승인에 실패했어요.')
  } finally {
    busyReqId.value = null
  }
}

function openReject(r: ProductRequest) {
  rejecting.value = r
  rejectReason.value = ''
}
function closeReject() {
  rejecting.value = null
}
async function confirmReject() {
  if (!rejecting.value) return
  busyReqId.value = rejecting.value.id
  try {
    const updated = await marketApi.rejectRequest(rejecting.value.id, rejectReason.value.trim() || null)
    upsertRequest(updated)
    closeReject()
  } catch (e) {
    alert(e instanceof ApiError ? e.message : '거절에 실패했어요.')
  } finally {
    busyReqId.value = null
  }
}

const statusText: Record<string, string> = {
  on_sale: '판매중',
  sold_out: '품절',
  hidden: '숨김',
}

const reqStatusText: Record<string, string> = {
  pending: '검토 대기',
  approved: '승인됨',
  rejected: '거절됨',
}

onMounted(async () => {
  await load()
  connect()
})
</script>

<template>
  <main class="jc-shell">
    <div class="head">
      <h1 class="jc-title page-title">대장마켓</h1>
      <button v-if="tab === 'products'" class="add" @click="openNew">+ 상품</button>
    </div>

    <div class="seg">
      <button class="seg__btn" :class="{ 'seg__btn--on': tab === 'products' }" @click="tab = 'products'">
        상품 ({{ products.length }})
      </button>
      <button class="seg__btn" :class="{ 'seg__btn--on': tab === 'orders' }" @click="tab = 'orders'">
        주문 <span v-if="pendingOrders.length" class="badge">{{ pendingOrders.length }}</span>
      </button>
      <button class="seg__btn" :class="{ 'seg__btn--on': tab === 'requests' }" @click="tab = 'requests'">
        신청 <span v-if="pendingRequests.length" class="badge">{{ pendingRequests.length }}</span>
      </button>
    </div>

    <p v-if="loading" class="jc-muted center">불러오는 중…</p>

    <!-- 상품 관리 -->
    <template v-else-if="tab === 'products'">
      <p v-if="!products.length" class="empty">
        아직 상품이 없어요.<br />오른쪽 위 <b>+ 상품</b>으로 첫 상품을 올려보세요.
      </p>
      <div v-for="p in products" :key="p.id" class="prow" :class="{ 'prow--hidden': p.status === 'hidden' }">
        <div class="prow__thumb">
          <img v-if="p.image_url" :src="p.image_url" :alt="p.name" />
          <span v-else>🎁</span>
        </div>
        <div class="prow__info">
          <b class="prow__name">{{ p.name }}</b>
          <small class="prow__meta">
            🪙 {{ p.price_coin.toLocaleString() }}
            · <span :class="`st st--${p.status}`">{{ statusText[p.status] }}</span>
            <template v-if="p.stock !== null"> · 재고 {{ p.stock }}</template>
          </small>
        </div>
        <div class="prow__actions">
          <button class="mini mini--ghost" @click="openEdit(p)">수정</button>
          <button class="mini mini--ghost" @click="toggleHidden(p)">{{ p.status === 'hidden' ? '공개' : '숨김' }}</button>
          <button class="mini mini--del" @click="removeProduct(p)">삭제</button>
        </div>
      </div>
    </template>

    <!-- 주문 관리 -->
    <template v-else-if="tab === 'orders'">
      <p v-if="!orders.length" class="empty">아직 들어온 주문이 없어요.</p>
      <div v-for="o in orders" :key="o.id" class="orow" :class="{ 'orow--done': o.status === 'fulfilled' }">
        <div class="prow__thumb">
          <img v-if="o.product_image_url" :src="o.product_image_url" :alt="o.product_name" />
          <span v-else>🎁</span>
        </div>
        <div class="prow__info">
          <b class="prow__name">{{ o.product_name }}</b>
          <small class="prow__meta">{{ o.buyer_name }} · 🪙 {{ o.price_paid.toLocaleString() }}</small>
        </div>
        <button
          v-if="o.status === 'purchased'"
          class="mini mini--fulfill"
          :disabled="busyOrderId === o.id"
          @click="fulfill(o)"
        >
          수령완료
        </button>
        <span v-else class="chip-done">✓ 완료</span>
      </div>
    </template>

    <!-- 상품 신청 관리 -->
    <template v-else>
      <p v-if="!requests.length" class="empty">
        아직 들어온 상품 신청이 없어요.<br />쫄병이 갖고 싶은 상품을 신청하면 여기 나타나요.
      </p>
      <div v-for="r in requests" :key="r.id" class="reqrow" :class="{ 'reqrow--done': r.status !== 'pending' }">
        <div class="reqrow__top">
          <div class="prow__thumb">
            <img v-if="r.image_url" :src="r.image_url" :alt="r.name" />
            <span v-else>📝</span>
          </div>
          <div class="prow__info">
            <b class="prow__name">{{ r.name }}</b>
            <small class="prow__meta">
              {{ r.requester_name }} · 희망가 🪙 {{ r.desired_price.toLocaleString() }}
            </small>
          </div>
          <span v-if="r.status !== 'pending'" class="chip-req" :class="`chip-req--${r.status}`">
            {{ reqStatusText[r.status] }}
          </span>
        </div>

        <p v-if="r.description" class="reqrow__desc">{{ r.description }}</p>
        <a v-if="r.reference_url" class="reqrow__link" :href="r.reference_url" target="_blank" rel="noopener">
          🔗 참고 링크
        </a>
        <p v-if="r.status === 'rejected' && r.reject_reason" class="reqrow__reason">
          거절 사유: {{ r.reject_reason }}
        </p>

        <div v-if="r.status === 'pending'" class="reqrow__actions">
          <button class="mini mini--fulfill" :disabled="busyReqId === r.id" @click="approveRequest(r)">
            승인 → 등록
          </button>
          <button class="mini mini--del" :disabled="busyReqId === r.id" @click="openReject(r)">
            거절
          </button>
        </div>
      </div>
    </template>

    <!-- 상품 등록/수정 시트 -->
    <transition name="sheet">
      <div v-if="showForm" class="sheet-wrap" @click.self="closeForm">
        <div class="sheet">
          <div class="sheet__grab" />
          <p class="sheet__title">{{ editing ? '상품 수정' : '새 상품 등록' }}</p>

          <button type="button" class="uploader" @click="($refs.fileInput as HTMLInputElement).click()">
            <img v-if="form.image_url" :src="form.image_url" alt="상품 이미지" class="uploader__img" />
            <span v-else class="uploader__ph">
              {{ uploading ? '업로드 중…' : '📷 대표 이미지 추가' }}
            </span>
            <span v-if="form.image_url && !uploading" class="uploader__edit">변경</span>
          </button>
          <input ref="fileInput" type="file" accept="image/*" hidden @change="onFile" />

          <label class="jc-label">상품 이름</label>
          <input v-model="form.name" class="jc-input" placeholder="예: 편의점 간식" maxlength="100" />

          <div class="two">
            <div>
              <label class="jc-label">가격(코인)</label>
              <input v-model.number="form.price_coin" class="jc-input" type="number" min="1" inputmode="numeric" />
            </div>
            <div>
              <label class="jc-label">재고 <span class="opt">(비우면 무제한)</span></label>
              <input v-model="form.stock" class="jc-input" type="number" min="0" inputmode="numeric" placeholder="∞" />
            </div>
          </div>

          <label class="jc-label">설명 <span class="opt">(선택)</span></label>
          <textarea v-model="form.description" class="jc-input area" rows="2" placeholder="상품 설명을 적어주세요" maxlength="2000" />

          <p v-if="formError" class="jc-error">{{ formError }}</p>

          <button class="jc-btn jc-btn--primary sheet__submit" :disabled="saving || uploading" @click="save">
            {{ saving ? '저장 중…' : editing ? '수정 완료' : '상품 등록' }}
          </button>
          <button class="jc-btn jc-btn--ghost" @click="closeForm">취소</button>
        </div>
      </div>
    </transition>

    <!-- 신청 거절 사유 시트 -->
    <transition name="sheet">
      <div v-if="rejecting" class="sheet-wrap" @click.self="closeReject">
        <div class="sheet">
          <div class="sheet__grab" />
          <p class="sheet__title">신청 거절</p>
          <p class="reject__target">‘{{ rejecting.name }}’ 신청을 거절해요.</p>

          <label class="jc-label">거절 사유 <span class="opt">(선택)</span></label>
          <textarea
            v-model="rejectReason"
            class="jc-input area"
            rows="2"
            placeholder="쫄병에게 보여줄 사유를 적어주세요 (비워도 돼요)"
            maxlength="255"
          />

          <button
            class="jc-btn jc-btn--primary sheet__submit"
            :disabled="busyReqId === rejecting.id"
            @click="confirmReject"
          >
            거절하기
          </button>
          <button class="jc-btn jc-btn--ghost" @click="closeReject">취소</button>
        </div>
      </div>
    </transition>
  </main>
</template>

<style scoped>
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 4px 0 14px;
}
.page-title {
  font-size: 26px;
  margin: 0;
}
.add {
  border: none;
  background: var(--coral);
  color: #fff;
  font-family: var(--font-display);
  font-size: 14px;
  padding: 8px 14px;
  border-radius: 12px;
  cursor: pointer;
  box-shadow: 0 6px 14px -8px rgba(240, 79, 62, 0.7);
}
.add:active {
  transform: translateY(1px);
}
.center {
  text-align: center;
  margin-top: 30px;
}

.seg {
  display: flex;
  gap: 6px;
  background: #eef1f5;
  padding: 4px;
  border-radius: 14px;
  margin-bottom: 16px;
}
.seg__btn {
  flex: 1;
  padding: 9px 0;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--ink-soft);
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
}
.seg__btn--on {
  background: #fff;
  color: var(--ink);
  box-shadow: 0 1px 4px rgba(22, 32, 46, 0.1);
}
.badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  display: inline-grid;
  place-items: center;
  border-radius: 999px;
  background: var(--coral);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.empty {
  padding: 34px 18px;
  text-align: center;
  font-size: 13.5px;
  line-height: 1.7;
  color: var(--ink-faint);
  background: var(--paper);
  border: 1px dashed var(--line-strong);
  border-radius: 16px;
}

.prow,
.orow {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 13px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 14px;
  margin-bottom: 8px;
}
.prow--hidden {
  opacity: 0.6;
}
.orow--done {
  opacity: 0.65;
}
.prow__thumb {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #fff7e6, #fdeecb);
  overflow: hidden;
  font-size: 22px;
  flex-shrink: 0;
}
.prow__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.prow__info {
  flex: 1;
  min-width: 0;
}
.prow__name {
  font-size: 14.5px;
  color: var(--ink);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.prow__meta {
  font-size: 12.5px;
  color: var(--ink-faint);
}
.st--on_sale {
  color: #0f8f52;
}
.st--sold_out {
  color: var(--coral-deep);
}
.st--hidden {
  color: var(--ink-faint);
}
.prow__actions {
  display: flex;
  gap: 5px;
  flex-shrink: 0;
}
.mini {
  padding: 7px 10px;
  border-radius: 10px;
  border: none;
  font-weight: 700;
  font-size: 12.5px;
  cursor: pointer;
  transition: filter 0.15s, transform 0.1s;
}
.mini:active {
  transform: scale(0.95);
}
.mini:disabled {
  opacity: 0.5;
}
.mini--ghost {
  background: #fff;
  border: 1.5px solid var(--line-strong);
  color: var(--ink-soft);
}
.mini--del {
  background: #fff;
  border: 1.5px solid #ffd9d3;
  color: var(--coral-deep);
}
.mini--fulfill {
  background: var(--mint);
  color: #fff;
  flex-shrink: 0;
}
.chip-done {
  font-size: 12.5px;
  font-weight: 700;
  color: #0f8f52;
  flex-shrink: 0;
}

/* 상품 신청 */
.reqrow {
  padding: 12px 13px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 14px;
  margin-bottom: 8px;
}
.reqrow--done {
  opacity: 0.72;
}
.reqrow__top {
  display: flex;
  align-items: center;
  gap: 12px;
}
.reqrow__desc {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--ink-soft);
  white-space: pre-wrap;
}
.reqrow__link {
  display: inline-block;
  margin-top: 8px;
  font-size: 12.5px;
  font-weight: 700;
  color: var(--coral-deep);
  text-decoration: none;
}
.reqrow__reason {
  margin: 8px 0 0;
  font-size: 12.5px;
  color: var(--coral-deep);
}
.reqrow__actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.reqrow__actions .mini {
  flex: 1;
  padding: 10px 0;
  text-align: center;
}
.chip-req {
  font-size: 11.5px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  flex-shrink: 0;
}
.chip-req--approved {
  background: rgba(35, 194, 116, 0.15);
  color: #0f8f52;
}
.chip-req--rejected {
  background: #ffe9e5;
  color: var(--coral-deep);
}
.reject__target {
  margin: 0 0 14px;
  font-size: 13.5px;
  color: var(--ink-soft);
}
.opt {
  color: var(--ink-faint);
  font-weight: 400;
}

/* 시트 */
.sheet-wrap {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(22, 32, 46, 0.4);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.sheet {
  width: 100%;
  max-width: 30rem;
  background: var(--paper);
  border-radius: 26px 26px 0 0;
  padding: 10px 20px calc(24px + env(safe-area-inset-bottom));
  box-shadow: 0 -12px 40px -12px rgba(22, 32, 46, 0.4);
  max-height: 92vh;
  overflow-y: auto;
}
.sheet__grab {
  width: 40px;
  height: 4px;
  border-radius: 999px;
  background: var(--line-strong);
  margin: 4px auto 14px;
}
.sheet__title {
  margin: 0 0 14px;
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--ink);
}
.uploader {
  width: 100%;
  aspect-ratio: 16 / 9;
  border: 2px dashed var(--line-strong);
  border-radius: 16px;
  background: #faf8f4;
  display: grid;
  place-items: center;
  cursor: pointer;
  overflow: hidden;
  position: relative;
  margin-bottom: 14px;
}
.uploader__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.uploader__ph {
  color: var(--ink-faint);
  font-weight: 700;
  font-size: 14px;
}
.uploader__edit {
  position: absolute;
  right: 10px;
  bottom: 10px;
  background: rgba(22, 32, 46, 0.72);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
}
.two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.area {
  resize: none;
  font-family: var(--font-body);
  line-height: 1.5;
}
.sheet__submit {
  margin: 12px 0 8px;
}

.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.2s ease;
}
.sheet-enter-active .sheet,
.sheet-leave-active .sheet {
  transition: transform 0.24s cubic-bezier(0.32, 0.72, 0, 1);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .sheet,
.sheet-leave-to .sheet {
  transform: translateY(100%);
}
</style>
