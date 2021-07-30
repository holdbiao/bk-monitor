<template>
  <div class="data-query-history-item" v-bkloading="{ isLoading: comLoading }">
    <div class="history-header" @click="handleShowContent">
      <div class="header-left">
        <i :class="['icon-monitor', 'icon-arrow-down', { 'arrow-right': !isShowContent }]"></i>
        <div class="title" v-if="data.name">{{ data.name }}</div>
        <div v-else @click.stop class="input-wrapper">
          <bk-input
            v-model="nameValue"
            ref="titleInput"
            @blur="handleEnter"
            @enter="handleEnter"></bk-input>
        </div>
      </div>
      <div class="header-right" v-if="data.name">
        <i class="icon-monitor icon icon-bofang" v-bk-tooltips="$t('再次查询')" @click.stop="queryAgain"></i>
        <i class="icon-monitor icon icon-mc-delete-line" @click.stop="deleteHistoryItem"></i>
      </div>
    </div>
    <div :class="['des-content']" ref="contentWrapper">
      <div class="des-main" ref="content">
        <!-- 展示数据是图表查询params TODO -->
        {{ getDescString }}
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Ref } from 'vue-property-decorator'
import MonitorVue from '../../../types/index'
import { IHistoryListItem } from '../index'
import DataRetrieval from '../../../store/modules/data-retrieval'

@Component({
  name: 'data-query-history-item'
})
export default class DataQueryHistoryItem extends Vue<MonitorVue> {
  @Prop({ default: () => [], required: true, type: Object }) readonly data: IHistoryListItem
  @Prop({ required: true, type: Number }) readonly index: number

  @Ref('content') readonly contentEl: HTMLElement
  @Ref('contentWrapper') readonly contentWrapperEl: HTMLElement
  @Ref('titleInput') readonly bkInputEl: Vue

  isShowContent = false
  nameValue = ''
  comLoading = false

  get getDescString() {
    return JSON.stringify(this.data.config.queryConfigs, (key: string, value: string) => {
      const deleKeyMap = ['hidden', 'name', 'label', 'merticVal', 'key']
      if (deleKeyMap.includes(key)) {
        return undefined
      }
      return value
    })
  }

  created() {
    if (!this.data.name) this.isShowContent = true
  }

  mounted() {
    this.isShowContent && this.showContent()
  }

  activated() {
    if (!this.data.name) {
      const inputEL = this.bkInputEl.$el.querySelector('input')
      inputEL.focus()
    }
  }

  // 展开查询条件
  handleShowContent() {
    this.isShowContent = !this.isShowContent
    this.showContent()
  }

  showContent() {
    const el = this.contentEl
    const cont = this.contentWrapperEl
    if (!el) return
    const h = el.scrollHeight
    if (cont.style.height) {
      cont.style.height = null
    } else {
      cont.style.height = `${h}px`
    }
  }

  // 再次查询
  queryAgain() {
    DataRetrieval.queryAgain(this.index)
  }

  // 删除历史
  async deleteHistoryItem() {
    this.comLoading = true
    const data = DataRetrieval.deleteQueryHistory(this.index).catch(() => ({}))
      .finally(() => this.comLoading = false)
    return data
  }

  // 保存历史标题
  handleEnter() {
    this.comLoading = true
    DataRetrieval.saveQueryHistory(this.nameValue).then(() => {
      this.nameValue = ''
    })
      .finally(() => this.comLoading = false)
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.data-query-history-item {
  border-bottom: 1px solid #f0f1f5;
  .history-header {
    display: flex;
    align-items: center;
    height: 42px;
    padding: 0 16px 0 14px;
    cursor: pointer;
    .header-left {
      flex: 1;
      display: flex;
      align-items: center;
      .title {
        font-size: 12px;
        color: #313238;
        line-height: 20px;
      }
      .icon-arrow-down {
        margin-right: 6px;
      }
      .input-wrapper {
        flex: 1;
      }
    }
    .header-right {
      flex-shrink: 0;
      display: flex;
      align-items: center;
      .icon {
        display: inline-block;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        font-size: 16px;
        cursor: pointer;
        &::before {
          width: 100%;
          height: 100%;

          @include content-center;
        }
      }
      .icon-bofang {
        &:hover {
          color: $primaryFontColor;
          background-color: #e1ecff;
        }
      }
    }
  }
  .des-content {
    height: 0;
    overflow: hidden;
    will-change: height;
    transition: height .3s ease-in-out;
    .des-main {
      padding: 7px 46px 21px 44px;
      line-height: 20px;
      font-size: 12px;
      word-break: break-all;
      color: #979ba5;
    }
  }
  .des-hidden {
    padding: 0 46px 0 44px;
  }
}
</style>
