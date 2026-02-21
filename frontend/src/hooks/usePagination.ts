import { useState } from 'react'

export function usePagination(initialPage = 1, initialPageSize = 20) {
  const [page, setPage] = useState(initialPage)
  const [pageSize] = useState(initialPageSize)

  const nextPage = () => setPage((p) => p + 1)
  const prevPage = () => setPage((p) => Math.max(1, p - 1))
  const goToPage = (n: number) => setPage(n)
  const reset = () => setPage(1)

  return { page, pageSize, nextPage, prevPage, goToPage, reset }
}
