import { useEffect, useRef } from 'react'

const FOCUSABLE = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export const useAccessibleModal = (isOpen: boolean, onClose: () => void) => {
  const modalRef = useRef<HTMLDivElement>(null)
  const onCloseRef = useRef(onClose)

  useEffect(() => {
    onCloseRef.current = onClose
  }, [onClose])

  useEffect(() => {
    if (!isOpen || !modalRef.current) return

    const container = modalRef.current
    const previousFocus = document.activeElement as HTMLElement | null
    const focusables = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE))
    ;(focusables[0] ?? container).focus()

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onCloseRef.current()
        return
      }

      if (event.key !== 'Tab') return
      const currentFocusables = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE))
      if (currentFocusables.length === 0) {
        event.preventDefault()
        container.focus()
        return
      }

      const first = currentFocusables[0]
      const last = currentFocusables[currentFocusables.length - 1]
      const active = document.activeElement as HTMLElement | null

      if (event.shiftKey && active === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && active === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      previousFocus?.focus?.()
    }
  }, [isOpen])

  return modalRef
}
