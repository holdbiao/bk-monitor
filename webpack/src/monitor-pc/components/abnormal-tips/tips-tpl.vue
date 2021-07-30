<template>
  <div class="abnormal-tips-wrap">
    <div :class="['content-wrap', { 'content-en': lang === 'en' }]">
      <span class="text">{{ $attrs['tips-text'] }}</span>
      <span
        v-if="$attrs['link-url'] && $attrs['link-text']"
        class="link"
        @click="handleOpenLink($attrs['link-url'])">{{ $attrs['link-text'] }}<span class="icon-monitor icon-mc-link"></span></span>
      <span
        v-if="$attrs['doc-link']"
        class="link"
        @click="handleGotoLink($attrs['doc-link'])">{{ $t('请查看文档') }}<span class="icon-monitor icon-mc-link"></span></span>
    </div>
  </div>
</template>
<script lang="ts">
import { Component, Mixins } from 'vue-property-decorator'
import documentLinkMixin from '../../mixins/documentLinkMixin'
import { getCookie } from '../../../monitor-common/utils/utils'

// zh-cn
@Component({
  name: 'abnormal-tips'
})
export default class AbnormalTips extends Mixins(documentLinkMixin) {
  public handleOpenLink(url: string) {
    window.open(url, '_blank')
  }

  private get lang() {
    const lan = getCookie('blueking_language')
    return lan === 'en' ? 'en' : 'cn'
  }
}
</script>
<style lang="scss">
.abnormal-tips-wrap {
  padding: 5px;
  .content-wrap {
    width: 195px;
    font-size: 0;
    span {
      font-size: 12px;
      line-height: 20px;
    }
    .link {
      white-space: nowrap;
      color: #3a84ff;
      cursor: pointer;
      .icon-mc-link {
        margin-left: 4px;
      }
    }
  }
  .content-en {
    width: 300px;
  }
}
</style>
