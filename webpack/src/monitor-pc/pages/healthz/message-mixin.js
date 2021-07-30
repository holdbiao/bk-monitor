
const messageMixin = {
  data() {
    return {
      message: {}
    }
  },
  created() {
    ['error', 'success'].forEach((key) => {
      this.$set(this.message, key, message => this.$bkMessage({
        theme: key,
        message,
        ellipsisLine: 0
      }))
    })
  }
}

export {
  messageMixin
}
