<template>
  <div class="log-retrieval">
    <iframe ref="iframe" class="log-retrieval-frame" allow="fullscreen" :src="retrievalUrl"></iframe>
  </div>
</template>
<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
@Component({
  name: 'log-retrieval'
})
export default class LogRetrieval extends Vue {
  get retrievalUrl() {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line max-len
      // eslint-disable-next-line vue/max-len
      return `${process.env.loginHost}/t/log-search-4#/retrieve/?from=monitor&bizId=${this.$store.getters.bizId}&lang=zh`
    }
    return `${this.$store.getters.bkLogSearchUrl}#/retrieve/?from=monitor&bizId=${this.$store.getters.bizId}&lang=zh`
  }
}
</script>
<style lang="scss" scoped>
    .log-retrieval {
      // margin: -20px -24px 0;
      &-frame {
        width: 100%;
        min-width: 100%;
        min-height: calc(100vh - 55px);
        border: 0;
      }
    }
</style>
