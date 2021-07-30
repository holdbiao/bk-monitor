export default (userName: string): string => (userName
  ? `data:image/svg+xml;base64,${window.btoa(unescape(encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg"
 width="120" height="120" viewbox="0 0 120 120">
<text x="0"
  y="60"
  stroke="#aaa"
  stroke-width="1"
  stroke-opacity=".2"
  fill="none"
  transform="rotate(-45)"
  transform-origin="center"
  style="font-size: 12px;">
  ${userName}
</text>
</svg>`)))}`
  : '')
