export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pages: number
  page_size?: number
}
