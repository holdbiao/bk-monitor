<template>
  <div class="function-item-wrapper" v-bkloading="{ isLoading: loading }">
    <!-- 头部信息 -->
    <div class="title-wrapper" @click="handleShowDetail">
      <div class="left">
        <i :class="['icon-monitor', 'icon-Triangle-down', { 'icon-show-content': false }]"></i>
        <span class="title">{{data.displayName}}</span>
        <span class="des">{{`${$t('依赖:')} ${data.pluginId}`}}</span>
        <span class="status" v-if="data.hostCount.total !== '-'">{{`${$t('成功')}/${$t('总共')}:`}}<router-link to="uptime-check-node" class="count">{{data.hostCount && `${data.hostCount.success}/${data.hostCount.total}`}}</router-link></span>
      </div>
      <div class="switch-wrap">
        <bk-switcher
          class="switch-btn"
          theme="primary"
          v-model="isEnable"
          @change="handleFunctionSwitch">
        </bk-switcher>
        <div
          v-authority="{ active: !authority.MANAGE_AUTH }"
          v-if="!authority.MANAGE_AUTH"
          class="switch-wrap-modal"
          @click.stop.prevent="!authority.MANAGE_AUTH && handleShowAuthorityDetail()">
        </div>
      </div>
    </div>
    <!-- 展开内容:  产品后期需加入的功能, 暂不渲染此部分-->
    <div :class="['content-wrapper', { 'show-content': isShowContent }]" v-if="false">
      <div class="content-main" ref="content">
        <!-- 简介 -->
        <div class="des" v-if="data.content">{{data.content}}<a class="more">{{$t('查看更多')}}</a></div>
        <!-- 排除的主机列表 -->
        <bk-table
          v-if="data.list && data.list.length"
          class="table-wrapper"
          :outer-border="false"
          :data="data.list">
          <bk-table-column :label="$t('系统事件')" prop="name"></bk-table-column>
          <bk-table-column :label="$t('排除主机')" prop="host">
            <template slot-scope="props">
              <host-editable v-model="props.row.host"></host-editable>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('开关')" prop="status" align="right" width="120">
            <template slot-scope="props">
              <switcher v-model="props.row.status"></switcher>
            </template>
          </bk-table-column>
        </bk-table>
        <template v-if="data.excludes">
          <div class="label">{{$t('排除的主机列表:')}}</div>
          <bk-input
            :value="data.excludes"
            type="textarea"
            :rows="3">
          </bk-input>
          <div class="btn-wrapper">
            <span class="save">{{$t('保存')}}</span>
            <span class="cancel">{{$t('取消')}}</span>
            <span class="history">{{$t('更新执行历史')}}</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Ref, PropSync, Inject } from 'vue-property-decorator'
import Switcher from './switcher.vue'
import HostEditable from './host-editable.vue'
import { switchFunction } from '../../../monitor-api/modules/function_switch.js'
import MonitorVue from '../../types/index'

@Component({
  name: 'function-item',
  components: { Switcher, HostEditable }
})
export default class FunctionItem extends Vue<MonitorVue> {
  @Prop({ default: () => {}, required: true }) readonly data: any
  @PropSync('enable', { required: true, default: false }) isEnable: boolean
  @Inject('authority') authority
  @Inject('handleShowAuthorityDetail') handleShowAuthorityDetail
  // 详情展开状态
  isShowContent = true
  // loading
  loading = false

  @Ref('content') readonly cententEl: HTMLElement

  mounted() {
    this.isShowContent = this.data.show
    this.isShowContent && this.showDetail()
  }

  // 展开/收缩详情
  handleShowDetail() {
    this.isShowContent = !this.isShowContent
    this.showDetail()
  }

  // 控制内容展开
  showDetail() {
    const el = this.cententEl
    if (!el) return
    const height = el.scrollHeight
    if (el.style.height) {
      el.style.height = null
    } else {
      el.style.height = `${height}px`
    }
  }

  // 功能开关
  handleFunctionSwitch(v: boolean) {
    if (this.authority.MANAGE_AUTH) {
      const params = {
        id: this.data.id,
        is_enable: v
      }
      this.loading = true
      switchFunction(params).then(() => {
        this.$bkMessage({ theme: 'success', message: this.$t(v ? '开启成功' : '关闭成功') })
      })
        .catch(() => {
        // 报错则恢复原状态
          this.isEnable = !v
        })
        .finally(() => (this.loading = false))
    } else {
      this.isEnable = !v
    }
  }
}
</script>

<style lang="scss" scoped>
  @import "../../static/css/common.scss";

  .function-item-wrapper {
    min-height: 64px;
    border-radius: 2px;
    background-color: #fff;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, .05);
    .title-wrapper {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 64px;
      padding: 0 24px 0 10px;
      color: $defaultFontColor;
      // cursor: pointer;
      .left {
        display: flex;
        align-items: center;
        .icon-Triangle-down {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          font-size: 20px;
          &::before {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            transform: rotate(-90deg);
            transition: all .3s ease;
          }
        }
        .icon-show-content {
          &::before {
            transform: rotate(0deg);
          }
        }
      }
      .title {
        display: inline-block;
        width: 264px;
        font-size: 14px;
        font-weight: 700;
      }
      .des {
        display: inline-block;
        width: 255px;
        font-size: 12px;
      }
      .status {
        .count {
          color: $primaryFontColor;
        }
      }
      .switch-wrap {
        position: relative;
        &-modal {
          position: absolute;
          left: 0;
          right: 0;
          top: 0;
          bottom: 0;
          background: transparent;
          z-index: 29;
          &:hover {
            cursor: pointer;
          }
        }
      }
      .switch-btn {
        justify-self: end;
      }
    }
    .content-wrapper {
      padding: 0 24px;
      .content-main {
        will-change: height;
        height: 0;
        overflow: hidden;
        transition: all .3s cubic-bezier(.4, 0, .2, 1);
      }
      .des {
        line-height: 20px;
        .more {
          margin-left: 10px;
          color: $primaryFontColor;
          cursor: pointer;
        }
      }
      /deep/.table-wrapper {
        margin-top: 17px;
        overflow: hidden;
        &::before {
          background: none;
        }
        .bk-table-body-wrapper {
          overflow: visible;
        }
        .bk-table-row {
          .cell {
            overflow: visible;
          }
        }
      }
      .label {
        margin-top: 10px;
        margin-bottom: 5px;
      }
      .btn-wrapper {
        height: 20px;
        line-height: 20px;
        margin-top: 5px;
        font-size: 12px;
        color: $primaryFontColor;
        .save,
        .cancel {
          float: left;
          cursor: pointer;
        }
        .cancel {
          margin-left: 16px;
          color: $defaultFontColor;
        }
        .history {
          float: right;
          cursor: pointer;
        }
      }
    }
    .show-content {
      padding: 0 24px 24px 24px;
    }
  }
</style>
