export default {
  data() {
    return {
      log: {
        show: false
      }
    }
  },
  mounted() {
    this.handleSetVersionLog()
  },
  methods: {
    // 设置版本日志是否显示
    handleSetVersionLog() {
      if (this.getCookie('SHOW_VERSION_LOG') === 'True') {
        this.log.show = true
        document.cookie = 'SHOW_VERSION_LOG=; path=/; expire=Thu, 01 Jan 1970 00:00:01 GMT;'
      }
    },
    getCookie(name) {
      const reg = new RegExp(`(^|)${name}=([^;]*)(;|$)`)
      const data = document.cookie.match(reg)
      if (data) {
        return unescape(data[2])
      }
      return null
    }
  }
}
