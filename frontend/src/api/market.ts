import { api, tokens } from '@/lib/http'

export type ProductStatus = 'on_sale' | 'sold_out' | 'hidden'
export type OrderStatus = 'purchased' | 'fulfilled' | 'canceled'
export type ProductRequestStatus = 'pending' | 'approved' | 'rejected'

export interface Product {
  id: number
  name: string
  price_coin: number
  description: string | null
  image_url: string | null
  status: ProductStatus
  stock: number | null
  created_at: string
}

export interface Order {
  id: number
  product_id: number
  product_name: string
  product_image_url: string | null
  buyer_user_id: number
  buyer_name: string
  price_paid: number
  status: OrderStatus
  created_at: string
  fulfilled_at: string | null
}

export interface ProductInput {
  name: string
  price_coin: number
  description?: string | null
  image_url?: string | null
  stock?: number | null
}

export interface PurchaseResult {
  order_id: number
  product_id: number
  price_paid: number
  balance: number
}

export interface ProductRequest {
  id: number
  name: string
  desired_price: number
  description: string | null
  image_url: string | null
  reference_url: string | null
  status: ProductRequestStatus
  reject_reason: string | null
  product_id: number | null
  requester_user_id: number
  requester_name: string
  created_at: string
  decided_at: string | null
}

export interface ProductRequestInput {
  name: string
  desired_price: number
  description?: string | null
  image_url?: string | null
  reference_url?: string | null
}

/** 이미지 업로드 (multipart). http 래퍼는 JSON 전용이라 여기서 직접 fetch. */
async function uploadImage(file: File): Promise<{ image_url: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/market/upload', {
    method: 'POST',
    headers: tokens.access ? { Authorization: `Bearer ${tokens.access}` } : {},
    body: form,
  })
  if (!res.ok) {
    let detail = '이미지 업로드에 실패했어요.'
    try {
      const err = await res.json()
      if (typeof err.detail === 'string') detail = err.detail
    } catch {
      /* noop */
    }
    throw new Error(detail)
  }
  return res.json()
}

export const marketApi = {
  // 대장: 상품
  products: () => api<Product[]>('/market/products'),
  createProduct: (data: ProductInput) =>
    api<Product>('/market/products', { method: 'POST', body: data }),
  updateProduct: (id: number, data: Partial<ProductInput> & { status?: ProductStatus }) =>
    api<Product>(`/market/products/${id}`, { method: 'PATCH', body: data }),
  deleteProduct: (id: number) => api(`/market/products/${id}`, { method: 'DELETE' }),
  uploadImage,

  // 대장: 주문
  orders: () => api<Order[]>('/market/orders'),
  fulfill: (id: number) => api<Order>(`/market/orders/${id}/fulfill`, { method: 'POST' }),

  // 쫄병: 상점
  shop: () => api<Product[]>('/market/shop'),
  shopDetail: (id: number) => api<Product>(`/market/shop/${id}`),
  purchase: (id: number) =>
    api<PurchaseResult>(`/market/shop/${id}/purchase`, { method: 'POST' }),
  myOrders: () => api<Order[]>('/market/my-orders'),

  // 상품 신청 (쫄병 → 대장)
  createRequest: (data: ProductRequestInput) =>
    api<ProductRequest>('/market/requests', { method: 'POST', body: data }),
  myRequests: () => api<ProductRequest[]>('/market/my-requests'),
  requests: () => api<ProductRequest[]>('/market/requests'),
  approveRequest: (id: number) =>
    api<ProductRequest>(`/market/requests/${id}/approve`, { method: 'POST' }),
  rejectRequest: (id: number, reason?: string | null) =>
    api<ProductRequest>(`/market/requests/${id}/reject`, {
      method: 'POST',
      body: { reason: reason ?? null },
    }),
}
