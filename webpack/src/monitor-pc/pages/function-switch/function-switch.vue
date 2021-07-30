<template>
  <!-- 功能开关列表 -->
  <div class="function-switch-wrapper" v-monitor-loading="{ isLoading: loading }">
    <!-- 功能item -->
    <template v-if="!isAbnormal">
      <function-item
        class="func-item"
        v-for="(item, index) in dataList"
        :key="index"
        :data="item"
        :enable.sync="item.isEnable">
      </function-item>
    </template>
    <!-- 列表数据异常 -->
    <div v-else class="abnormal-data">
      <img class="abnormal-img" src="../../static/images/svg/Abnormal-data.svg" />
      <div class="abnormal-text">{{$t('拉取用户配置数据失败')}}</div>
      <bk-button theme="primary" @click="getFunctionList">{{$t('重新获取')}}</bk-button>
    </div>
  </div>
</template>

<script lang='ts'>
import { Component, Mixins, Provide } from 'vue-property-decorator'
import FunctionItem from './function-item.vue'
import { listFunction } from '../../../monitor-api/modules/function_switch.js'
import { transformDataKey } from '../../../monitor-common/utils/utils'
import * as funcAuth from './authority-map'
import authorityMixinCreate from '../../mixins/authorityMixin'
@Component({
  name: 'function-switch',
  components: { FunctionItem }
})
export default class FunctionSwitch extends Mixins(authorityMixinCreate(funcAuth)) {
  // 功能列表数据
  dataList: any = []
  loading = false
  // 数据异常
  isAbnormal = false
  @Provide('authority') authority
  @Provide('handleShowAuthorityDetail') handleShowAuthorityDetail
  created() {
    // 初始化数据
    this.getFunctionList()
  }

  // 获取功能列表数据
  getFunctionList() {
    this.loading = true
    listFunction().then((data) => {
      this.dataList = transformDataKey(data)
      this.isAbnormal = false
    })
      .catch(() => {
        this.isAbnormal = true
      })
      .finally(() => (this.loading = false))
  }
}
</script>

<style lang="scss" scoped>
  @import "../../static/css/common.scss";

  .function-switch-wrapper {
    padding-bottom: 20px;
    .func-item {
      &:not(:last-child) {
        margin-bottom: 10px;
      }
    }
    .abnormal-data {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-top: 22px;
      .abnormal-img {
        display: inline-block;
        width: 480px;
        height: 240px;
      }
      .abnormal-text {
        font-size: 24px;
        line-height: 31px;
        margin-bottom: 24px;
        color: $defaultFontColor;
      }
    }
  }
</style>
