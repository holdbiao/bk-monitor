<template>
  <!--公共组件按钮加tooltip-->
  <div>
    <el-tooltip popper-class="healthz-component-tooltip" effect="light" :placement="'bottom'">
      <div slot="content">
        <div class="content-tooltips-overflow">
          <div class="content-tooltip-h5" v-for="(tip, _index) in filteredNodeData" :key="_index"
               @click="showPopupDialog(tip)">
            <el-tooltip popper-class="healthz-component-tooltip" placement="top" :open-delay="500" effect="light">
              <div slot="content">{{tip.description}} {{tip.value}}</div>
              <h5 :class="{
                'class-success': tip.status === 0,
                'class-warning': tip.status === 1,
                'class-error': tip.status > 1 }">
                {{tip.server_ip}} {{tip.description}} {{tip.value}}
                <i class="reload-agent" v-show="tip.status > 1"> </i>
                <i class="warning-agent" v-show="tip.status === 1"></i>
              </h5>
            </el-tooltip>
          </div>
        </div>
        <div class="tooltip-footer">
          <div class="tooltip-success"></div>
          <span class="tooltip-text"> {{ $t('正常') }} </span>
          <div class="tooltip-warning"></div>
          <span class="tooltip-text"> {{ $t('关注') }} </span>
          <div class="tooltip-error"></div>
          <span class="tooltip-text"> {{ $t('异常') }} </span>
        </div>
      </div>
      <el-button class="btn-class-space" :class="{
        'class-success': color === 'green',
        'class-warning': color === 'yellow',
        'class-error': color === 'red',
        'class-normal': color === ''
      }">
        {{componentName}}
      </el-button>
    </el-tooltip>
    <mo-healthz-common-popup-window-view :is-visible.sync="isShowDialog"
                                         :tips="tips"></mo-healthz-common-popup-window-view>
    <div :class="status === 0 ? 'dash-border' : 'dotted-line'" :style="{ visibility: showLine }"
         v-if="!isLast">
    </div>
  </div>
</template>
<script>
import store from '../store/healthz/store'
import { Tooltip, Button } from 'element-ui'
import MoHealthzCommonPopupWindowView from './healthz-common-popup-window'
export default {
  name: 'MoHealthzComponentTooltipView',
  components: {
    MoHealthzCommonPopupWindowView,
    ElTooltip: Tooltip,
    ElButton: Button
  },
  props: {
    // 当前组件名称
    componentName: {
      type: String
    },
    // 是否展示连接线
    showLine: {
      type: String,
      default: 'hidden'
    },
    // 当前组件的位置，第一个组件不显示线
    index: {
      type: Number
    },
    // 是否是最后一个组件，用于控制是否渲染横线
    isLast: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      colors: ['green', 'yellow', 'red'], // 组件的颜色列表
      tips: {}, // 弹窗显示的数据
      isShowDialog: false // 是否显示当前弹窗
    }
  },
  computed: {
    saasComponentNeedToTest() {
      return store.state.saasComponentNeedToTest
    },
    selectedIPs() {
      return store.state.selectedIPs
    },
    globalData() {
      return store.state.globalData
    },
    // ...mapState([
    //     'saasComponentNeedToTest',
    //     'selectedIPs',
    //     'globalData'
    // ]),
    // 通过全局数据得到的本地数据
    nodeData() {
      const returnData = []
      const tmpGlobal = this.globalData
      for (let i = 0; i < tmpGlobal.length; i++) {
        if (this.componentName === tmpGlobal[i].node_name) {
          const tips = {}
          tips.server_ip = tmpGlobal[i].server_ip
          tips.description = tmpGlobal[i].description
          tips.value = tmpGlobal[i].result.value
          tips.name = tmpGlobal[i].node_name
          tips.message = tmpGlobal[i].result.message
          tips.status = tmpGlobal[i].result.status
          tips.solution = tmpGlobal[i].solution
          // 检查 result 中是否存在 api_list 存在的话，就放入tips
          if (Object.prototype.hasOwnProperty.call(tmpGlobal[i].result, 'api_list')) {
            tips.api_list = tmpGlobal[i].result.api_list
          }
          returnData.push(tips)
        }
      }
      return returnData
    },
    // 根据前端显示的选中的ip列表过滤本地数据
    filteredNodeData() {
      // 如果当前组件为saas依赖周边，则直接返回数据
      if (store.state.saasDependenciesComponent.indexOf(this.componentName) > -1) return this.nodeData
      const resultData = []
      for (let i = 0; i < this.nodeData.length; i++) {
        if (this.selectedIPs.indexOf(this.nodeData[i].server_ip) > -1) {
          resultData.push(this.nodeData[i])
        }
      }
      resultData.sort(this.compare)
      return resultData
    },
    // 当前节点所有数据的状态列表
    statusList() {
      const statusList = []
      const tmpGlobal = this.filteredNodeData
      for (let i = 0; i < tmpGlobal.length; i++) {
        if (this.componentName === tmpGlobal[i].name) {
          statusList.push(tmpGlobal[i].status)
        }
      }
      return statusList
    },
    // 由当前数据状态列表计算而来的颜色
    color() {
      // 无数据，则无颜色
      if (this.statusList.length === 0) return ''
      let max = Math.max.apply(null, this.statusList)
      max = max > 1 ? 2 : max
      return this.colors[max]
    },
    // 当前节点的状态，由所有数据的状态列表聚合而来，所有的状态都为0时才为0
    status() {
      // 如果没有数据，则认为出错
      if (this.statusList.length === 0) return 2
      const max = Math.max.apply(null, this.statusList)
      return max > 1 ? 2 : max
    }
  },
  methods: {
    // 显示当前弹窗，根据当前组件的不同，显示不同组件
    showPopupDialog(tips) {
      // 设置弹窗上的数据
      this.tips = tips
      this.isShowDialog = true
    },
    // 比较函数
    compare(obj1, obj2) {
      if (obj1.status > obj2.status) return -1
      if (obj1.status < obj2.status) return 1
      return 0
    }
  }
}
</script>
<style lang="scss" scoped>
    @import "../style/healthz";
</style>
<style>
    /* healthz页面下的tooltip样式 */
    .healthz-component-tooltip {
      /* stylelint-disable-next-line declaration-no-important */
      box-shadow: 0px 3px 4px 0px rgba(112, 115, 120, .1) !important;

      /* stylelint-disable-next-line declaration-no-important */
      border-radius: 2px !important;

      /* stylelint-disable-next-line declaration-no-important */
      border: solid 1px #e8eaec !important;
    }
</style>
