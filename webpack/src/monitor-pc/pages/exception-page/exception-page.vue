<template>
  <div class="exception-page">
    <bk-exception class="exception-page-img" :type="type">
      <template v-if="type + '' === '403'">
        <div class="exception-title">{{$t('您没有相应资源的访问权限，请申请权限或联系管理员授权')}}</div>
        <bk-button class="exception-btn" theme="primary" @click="handleGotoAppy">{{$t('去申请')}}</bk-button>
      </template>
    </bk-exception>
  </div>
</template>
<script lang="ts">
import { Prop, Component, Vue, Watch } from 'vue-property-decorator'
import { getAuthorityDetail } from '../../../monitor-api/modules/iam'
Component.registerHooks(['beforeRouteEnter'])
@Component({
  name: 'error-exception'
})
export default class ExceptionPage extends Vue {
  @Prop({ default: '404' }) type: string | number
  @Prop({ default: '' }) queryUid: string
  applyUrl = ''
  // beforeRouteEnter(to, from, next) {
  //   next(async (vm: ExceptionPage) => {
  //     const { actionId } = to.query
  //     if (actionId) {
  //       const data =  await getAuthorityDetail(
  //         { action_ids: Array.isArray(actionId) ? actionId : [actionId] }
  //         , { needMessage: false }
  //       ).catch(() => false)
  //       if (data) {
  //         vm.applyUrl = data.apply_url
  //       }
  //     }
  //   })
  // }
  @Watch('queryUid', { immediate: true })
  async onQeueryUidChange() {
    const { actionId } = this.$route.query
    if (actionId) {
      const data =  await getAuthorityDetail(
        { action_ids: Array.isArray(actionId) ? actionId : [actionId] }
        , { needMessage: false }
      ).catch(() => false)
      if (data) {
        this.applyUrl = data.apply_url
      }
    }
  }

  handleGotoAppy() {
    if (!this.applyUrl) return
    try {
      if (self === top) {
        window.open(this.applyUrl, '__blank')
      } else {
        top.BLUEKING.api.open_app_by_other('bk_iam', this.applyUrl)
      }
    } catch (_) {
      window.open(this.applyUrl, '__blank')
    }
  }
}
</script>
<style lang="scss" scoped>
.exception-page {
  height: 100%;
  display: flex;
  position: relative;
  justify-content: center;
  &-img {
    position: absolute;
    top: 40%;
    transform: translateY(-50%);
    max-width: 800px;
    .exception-btn {
      margin-top: 10px;
    }
  }
}
</style>
