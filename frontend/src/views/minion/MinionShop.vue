<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  marketApi,
  type Order,
  type Product,
  type ProductRequest,
  type ProductRequestInput,
} from '@/api/market'
import { useMarketStream } from '@/composables/useMarketStream'
import { useAuthStore } from '@/stores/auth'
import { ApiError } from '@/lib/http'

const auth = useAuthStore()

const products = ref<Product[]>([])
const myOrders = ref<Order[]>([])
const myRequests = ref<ProductRequest[]>([])
const loading = ref(true)
const balance = ref(auth.user?.balance ?? 0)

const tab = ref<'shop' | 'orders' | 'requests'>('shop')

// 상품 신청 폼
const showReqForm = ref(false)
const reqForm = ref<{
  name: string
  desired_price: number
  description: string
  reference_url: string
  image_url: string | null
}>({ name: '', desired_price: 100, description: '', reference_url: '', image_url: null })
const reqUploading = ref(false)
const reqSubmitting = ref(false)
const reqError = ref('')

// 구매 시트
const selected = ref<Product | null>(null)
const buying = ref(false)
const buyError = ref('')
const justBought = ref(false)

const onSale = computed(() => products.value.filter((p) => p.status !== 'hidden'))

async function load() {
  loading.value = true
  try {
    const [ps, os, rs] = await Promise.all([
      marketApi.shop(),
      marketApi.myOrders(),
      marketApi.myRequests(),
    ])
    products.value = ps
    myOrders.value = os
    myRequests.value = rs
  } finally {
    loading.value = false
  }
  // 최신 잔액 동기화
  await auth.refreshMe()
  balance.value = auth.user?.balance ?? balance.value
}

function upsertProduct(p: Product) {
  const i = products.value.findIndex((x) => x.id === p.id)
  if (i >= 0) products.value[i] = p
  else products.value.unshift(p)
}

const { connect } = useMarketStream({
  onProductCreated: upsertProduct,
  onProductUpdated: upsertProduct,
  onProductDeleted: (id) => {
    products.value = products.value.filter((p) => p.id !== id)
  },
  onRequestUpdated: (r) => {
    const i = myRequests.value.findIndex((x) => x.id === r.id)
    if (i >= 0) myRequests.value[i] = r
  },
})

function openBuy(p: Product) {
  if (p.status !== 'on_sale') return
  selected.value = p
  buyError.value = ''
  justBought.value = false
}
function closeBuy() {
  selected.value = null
}

const canAfford = computed(
  () => !!selected.value && balance.value >= selected.value.price_coin,
)

async function confirmBuy() {
  if (!selected.value) return
  buying.value = true
  buyError.value = ''
  try {
    const res = await marketApi.purchase(selected.value.id)
    balance.value = res.balance
    justBought.value = true
    // 주문 목록/상품 상태 갱신
    const [os] = await Promise.all([marketApi.myOrders()])
    myOrders.value = os
  } catch (e) {
    buyError.value = e instanceof ApiError ? e.message : '구매에 실패했어요.'
  } finally {
    buying.value = false
  }
}

const statusLabel: Record<string, string> = {
  purchased: '수령 대기',
  fulfilled: '수령 완료',
  canceled: '취소됨',
}

const reqStatusLabel: Record<string, string> = {
  pending: '검토 대기',
  approved: '승인됨',
  rejected: '거절됨',
}

const pendingReqCount = computed(
  () => myRequests.value.filter((r) => r.status === 'pending').length,
)

function openReqForm() {
  reqForm.value = {
    name: '',
    desired_price: 100,
    description: '',
    reference_url: '',
    image_url: null,
  }
  reqError.value = ''
  showReqForm.value = true
}
function closeReqForm() {
  showReqForm.value = false
}

async function onReqFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  reqUploading.value = true
  reqError.value = ''
  try {
    const { image_url } = await marketApi.uploadImage(file)
    reqForm.value.image_url = image_url
  } catch (err) {
    reqError.value = err instanceof Error ? err.message : '이미지 업로드에 실패했어요.'
  } finally {
    reqUploading.value = false
    input.value = ''
  }
}

async function submitRequest() {
  if (!reqForm.value.name.trim() || reqForm.value.desired_price <= 0) {
    reqError.value = '상품 이름과 희망 가격(1 이상)을 입력해 주세요.'
    return
  }
  reqSubmitting.value = true
  reqError.value = ''
  const payload: ProductRequestInput = {
    name: reqForm.value.name.trim(),
    desired_price: reqForm.value.desired_price,
    description: reqForm.value.description.trim() || null,
    reference_url: reqForm.value.reference_url.trim() || null,
    image_url: reqForm.value.image_url,
  }
  try {
    const created = await marketApi.createRequest(payload)
    myRequests.value.unshift(created)
    closeReqForm()
  } catch (e) {
    reqError.value = e instanceof ApiError ? e.message : '신청에 실패했어요.'
  } finally {
    reqSubmitting.value = false
  }
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
      <div class="wallet">🪙 {{ balance.toLocaleString() }}</div>
    </div>

    <div class="seg">
      <button class="seg__btn" :class="{ 'seg__btn--on': tab === 'shop' }" @click="tab = 'shop'">
        상점
      </button>
      <button class="seg__btn" :class="{ 'seg__btn--on': tab === 'orders' }" @click="tab = 'orders'">
        내 구매 <span v-if="myOrders.length" class="seg__count">{{ myOrders.length }}</span>
      </button>
      <button class="seg__btn" :class="{ 'seg__btn--on': tab === 'requests' }" @click="tab = 'requests'">
        상품신청 <span v-if="pendingReqCount" class="seg__count">{{ pendingReqCount }}</span>
      </button>
    </div>

    <p v-if="loading" class="jc-muted center">불러오는 중…</p>

    <!-- 상점 -->
    <template v-else-if="tab === 'shop'">
      <p v-if="!onSale.length" class="empty">아직 등록된 상품이 없어요.<br />대장이 상품을 올리면 여기 나타나요.</p>
      <div v-else class="grid">
        <button
          v-for="p in onSale"
          :key="p.id"
          class="card"
          :class="{ 'card--out': p.status !== 'on_sale' }"
          @click="openBuy(p)"
        >
          <div class="card__img">
            <img v-if="p.image_url" :src="p.image_url" :alt="p.name" />
            <span v-else class="card__ph">🎁</span>
            <span v-if="p.status === 'sold_out'" class="card__badge">품절</span>
          </div>
          <div class="card__body">
            <p class="card__name">{{ p.name }}</p>
            <p class="card__price">🪙 {{ p.price_coin.toLocaleString() }}</p>
          </div>
        </button>
      </div>
    </template>

    <!-- 내 구매 -->
    <template v-else-if="tab === 'orders'">
      <p v-if="!myOrders.length" class="empty">아직 구매한 상품이 없어요.</p>
      <div v-for="o in myOrders" :key="o.id" class="order">
        <div class="order__thumb">
          <img v-if="o.product_image_url" :src="o.product_image_url" :alt="o.product_name" />
          <span v-else>🎁</span>
        </div>
        <div class="order__info">
          <b class="order__name">{{ o.product_name }}</b>
          <small class="order__meta">🪙 {{ o.price_paid.toLocaleString() }}</small>
        </div>
        <span class="chip" :class="`chip--${o.status}`">{{ statusLabel[o.status] }}</span>
      </div>
    </template>

    <!-- 상품 신청 -->
    <template v-else>
      <button class="req-add" @click="openReqForm">＋ 갖고 싶은 상품 신청하기</button>
      <p class="req-hint">대장에게 마켓에 올려달라고 요청해요. 승인되면 상점에 등록돼요.</p>

      <p v-if="!myRequests.length" class="empty">아직 신청한 상품이 없어요.</p>
      <div v-for="r in myRequests" :key="r.id" class="req">
        <div class="req__thumb">
          <img v-if="r.image_url" :src="r.image_url" :alt="r.name" />
          <span v-else>📝</span>
        </div>
        <div class="req__info">
          <b class="req__name">{{ r.name }}</b>
          <small class="req__meta">희망가 🪙 {{ r.desired_price.toLocaleString() }}</small>
          <small v-if="r.status === 'rejected' && r.reject_reason" class="req__reason">
            사유: {{ r.reject_reason }}
          </small>
        </div>
        <span class="chip" :class="`chip--req-${r.status}`">{{ reqStatusLabel[r.status] }}</span>
      </div>
    </template>

    <!-- 구매 바텀시트 -->
    <transition name="sheet">
      <div v-if="selected" class="sheet-wrap" @click.self="closeBuy">
        <div class="sheet">
          <div class="sheet__grab" />
          <template v-if="!justBought">
            <div class="detail__img">
              <img v-if="selected.image_url" :src="selected.image_url" :alt="selected.name" />
              <span v-else class="detail__ph">🎁</span>
            </div>
            <h2 class="detail__name">{{ selected.name }}</h2>
            <p v-if="selected.description" class="detail__desc">{{ selected.description }}</p>
            <p v-if="selected.stock !== null" class="detail__stock">남은 수량 {{ selected.stock }}개</p>
            <div class="detail__price">🪙 {{ selected.price_coin.toLocaleString() }} 코인</div>

            <p v-if="!canAfford" class="jc-error">코인이 {{ (selected.price_coin - balance).toLocaleString() }}개 부족해요.</p>
            <p v-else-if="buyError" class="jc-error">{{ buyError }}</p>

            <button
              class="jc-btn jc-btn--gold sheet__submit"
              :disabled="buying || !canAfford"
              @click="confirmBuy"
            >
              {{ buying ? '구매 중…' : `🪙 ${selected.price_coin.toLocaleString()} 코인으로 구매` }}
            </button>
            <button class="jc-btn jc-btn--ghost" @click="closeBuy">닫기</button>
          </template>

          <!-- 구매 완료 -->
          <div v-else class="done">
            <div class="done__emoji">🎉</div>
            <p class="done__title">구매 완료!</p>
            <p class="done__desc">
              <b>{{ selected.name }}</b> 을(를) 샀어요.<br />
              대장에게 수령 요청이 전달됐어요.
            </p>
            <p class="done__balance">남은 코인 🪙 {{ balance.toLocaleString() }}</p>
            <button class="jc-btn jc-btn--primary sheet__submit" @click="closeBuy">확인</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 상품 신청 시트 -->
    <transition name="sheet">
      <div v-if="showReqForm" class="sheet-wrap" @click.self="closeReqForm">
        <div class="sheet">
          <div class="sheet__grab" />
          <p class="sheet__title">상품 신청하기</p>

          <button type="button" class="uploader" @click="($refs.reqFile as HTMLInputElement).click()">
            <img v-if="reqForm.image_url" :src="reqForm.image_url" alt="참고 이미지" class="uploader__img" />
            <span v-else class="uploader__ph">{{ reqUploading ? '업로드 중…' : '📷 참고 이미지 (선택)' }}</span>
            <span v-if="reqForm.image_url && !reqUploading" class="uploader__edit">변경</span>
          </button>
          <input ref="reqFile" type="file" accept="image/*" hidden @change="onReqFile" />

          <label class="jc-label">상품 이름</label>
          <input v-model="reqForm.name" class="jc-input" placeholder="예: 레고 시티 소방서" maxlength="100" />

          <label class="jc-label">희망 가격(코인)</label>
          <input
            v-model.number="reqForm.desired_price"
            class="jc-input"
            type="number"
            min="1"
            inputmode="numeric"
          />

          <label class="jc-label">신청 사유 <span class="opt">(선택)</span></label>
          <textarea
            v-model="reqForm.description"
            class="jc-input area"
            rows="2"
            placeholder="왜 이 상품을 갖고 싶은지 적어주세요"
            maxlength="2000"
          />

          <label class="jc-label">참고 링크 <span class="opt">(선택)</span></label>
          <input
            v-model="reqForm.reference_url"
            class="jc-input"
            type="url"
            placeholder="https://..."
            maxlength="500"
          />

          <p v-if="reqError" class="jc-error">{{ reqError }}</p>

          <button
            class="jc-btn jc-btn--primary sheet__submit"
            :disabled="reqSubmitting || reqUploading"
            @click="submitRequest"
          >
            {{ reqSubmitting ? '신청 중…' : '대장에게 신청' }}
          </button>
          <button class="jc-btn jc-btn--ghost" @click="closeReqForm">취소</button>
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
.wallet {
  font-family: var(--font-display);
  font-size: 15px;
  color: var(--gold-edge);
  background: rgba(232, 149, 43, 0.12);
  padding: 6px 12px;
  border-radius: 999px;
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
.seg__count {
  font-size: 12px;
  color: var(--coral-deep);
}

.empty {
  padding: 34px 18px;
  text-align: center;
  font-size: 13.5px;
  line-height: 1.6;
  color: var(--ink-faint);
  background: var(--paper);
  border: 1px dashed var(--line-strong);
  border-radius: 16px;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.card {
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--paper);
  overflow: hidden;
  cursor: pointer;
  text-align: left;
  transition: transform 0.12s, box-shadow 0.15s;
}
.card:active {
  transform: scale(0.97);
}
.card--out {
  opacity: 0.62;
}
.card__img {
  position: relative;
  aspect-ratio: 1 / 1;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #fff7e6, #fdeecb);
}
.card__img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.card__ph {
  font-size: 44px;
}
.card__badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(22, 32, 46, 0.72);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 999px;
}
.card__body {
  padding: 10px 12px 13px;
}
.card__name {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 700;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card__price {
  margin: 0;
  font-family: var(--font-display);
  font-size: 15px;
  color: var(--gold-edge);
}

/* 내 구매 리스트 */
.order {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 13px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 14px;
  margin-bottom: 8px;
}
.order__thumb {
  width: 46px;
  height: 46px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #fff7e6, #fdeecb);
  overflow: hidden;
  font-size: 22px;
  flex-shrink: 0;
}
.order__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.order__info {
  flex: 1;
  min-width: 0;
}
.order__name {
  font-size: 14.5px;
  color: var(--ink);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.order__meta {
  font-size: 12.5px;
  color: var(--ink-faint);
}
.chip {
  font-size: 11.5px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 999px;
  flex-shrink: 0;
}
.chip--purchased {
  background: rgba(255, 201, 60, 0.18);
  color: var(--gold-edge);
}
.chip--fulfilled {
  background: rgba(35, 194, 116, 0.15);
  color: #0f8f52;
}
.chip--canceled {
  background: #f1f3f6;
  color: var(--ink-faint);
}
.chip--req-pending {
  background: rgba(255, 201, 60, 0.18);
  color: var(--gold-edge);
}
.chip--req-approved {
  background: rgba(35, 194, 116, 0.15);
  color: #0f8f52;
}
.chip--req-rejected {
  background: #ffe9e5;
  color: var(--coral-deep);
}

/* 상품 신청 */
.req-add {
  width: 100%;
  border: none;
  background: var(--coral);
  color: #fff;
  font-family: var(--font-display);
  font-size: 15px;
  padding: 13px 0;
  border-radius: 14px;
  cursor: pointer;
  box-shadow: 0 6px 14px -8px rgba(240, 79, 62, 0.7);
}
.req-add:active {
  transform: translateY(1px);
}
.req-hint {
  margin: 10px 2px 16px;
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--ink-faint);
  text-align: center;
}
.req {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 13px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 14px;
  margin-bottom: 8px;
}
.req__thumb {
  width: 46px;
  height: 46px;
  border-radius: 11px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #eef3ff, #e3ebfb);
  overflow: hidden;
  font-size: 22px;
  flex-shrink: 0;
}
.req__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.req__info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.req__name {
  font-size: 14.5px;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.req__meta {
  font-size: 12.5px;
  color: var(--ink-faint);
}
.req__reason {
  font-size: 12px;
  color: var(--coral-deep);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 신청 폼 (BossMarket 폼 스타일과 동일 톤) */
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
.area {
  resize: none;
  font-family: var(--font-body);
  line-height: 1.5;
}
.opt {
  color: var(--ink-faint);
  font-weight: 400;
}
.sheet__title {
  margin: 0 0 14px;
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--ink);
}

/* 바텀시트 */
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
.detail__img {
  aspect-ratio: 16 / 10;
  border-radius: 18px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #fff7e6, #fdeecb);
  overflow: hidden;
  margin-bottom: 14px;
}
.detail__img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.detail__ph {
  font-size: 64px;
}
.detail__name {
  font-family: var(--font-display);
  font-size: 22px;
  margin: 0 0 6px;
  color: var(--ink);
}
.detail__desc {
  margin: 0 0 10px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-soft);
  white-space: pre-wrap;
}
.detail__stock {
  margin: 0 0 8px;
  font-size: 12.5px;
  color: var(--ink-faint);
}
.detail__price {
  font-family: var(--font-display);
  font-size: 22px;
  color: var(--gold-edge);
  margin-bottom: 14px;
}
.sheet__submit {
  margin: 6px 0 8px;
}

.done {
  text-align: center;
  padding: 10px 0 4px;
}
.done__emoji {
  font-size: 52px;
}
.done__title {
  font-family: var(--font-display);
  font-size: 22px;
  margin: 8px 0 6px;
  color: var(--ink);
}
.done__desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink-soft);
  margin: 0 0 8px;
}
.done__balance {
  font-family: var(--font-display);
  color: var(--gold-edge);
  margin: 0 0 14px;
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
