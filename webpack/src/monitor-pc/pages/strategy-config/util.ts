// drag触发
interface IDragOption {
  min: number,
  max: number
}
export const handleMouseDown: Function = (
  e,
  tag: string,
  resetWidth = 200,
  option: IDragOption,
  setWidth
) => {
  let { target } = e

  while (target && target.dataset.tag !== tag) {
    target = target.parentNode
  }
  const rect = target.getBoundingClientRect()
  document.onselectstart = function () {
    return false
  }
  document.ondragstart = function () {
    return false
  }
  const handleMouseMove = (event) => {
    if (event.clientX - rect.left < resetWidth) {
      setWidth(0)
    } else {
      const w = Math.min(Math.max(option.min, event.clientX - rect.left), option.max)
      setWidth(w)
    }
  }
  const handleMouseUp = () => {
    document.body.style.cursor = ''
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    document.onselectstart = null
    document.ondragstart = null
  }
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}
export const handleMouseMove: Function = (e) => {
  let { target } = e
  while (target && target.dataset.tag !== 'resizeTarget') {
    target = target.parentNode
  }
}
