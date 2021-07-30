<template>
  <div class="host-detail" v-bkloading="{ isLoading }">
    <div class="host-detail-title">
      <i class="icon-monitor icon-double-up"
         @click="handleTogglePanel">
      </i>
      <span>{{ data.type === 'host' ? $t('主机详情') : $t('节点详情') }}</span>
    </div>
    <div class="host-detail-content">
      <ul>
        <template v-if="data.type === 'host'">
          <!-- 主机基本信息 -->
          <li class="host-info"
              v-for="item in hostInfo"
              :key="item.id">
            <span class="host-info-title">{{ `${item.title}:`}}</span>
            <div class="host-info-content">
              <!-- 状态 -->
              <span :class="item.value === 0 ? 'status-normal' : 'status-unkown'"
                    v-if="item.id === 'status'">
                {{ statusMap[item.value] }}
              </span>
              <div v-else-if="item.id === 'module'">
                <ul :class="{ 'module-expand': !showAllModule }">
                  <li class="module-item"
                      v-for="(data, index) in item.value"
                      :key="index">
                    {{ data.topo_link_display.join('-') }}
                  </li>
                </ul>
                <li class="module-item" v-if="item.value.length > 2">
                  <bk-button
                    class="btn"
                    text
                    @click="handleToggleModule">
                    {{ showAllModule ? $t('收起') : $t('展开') }}
                  </bk-button>
                </li>
              </div>
              <span v-else>{{ item.value || '--' }}</span>
              <i v-bk-tooltips="$t('查看详情')"
                 class="ml5 icon-monitor icon-mc-link"
                 v-if="item.link && item.value"
                 @click="handleToCmdbHost">
              </i>
              <i v-bk-tooltips="$t('点击复制')"
                 class="ml5 icon-monitor icon-mc-copy"
                 v-if="item.copy && item.value"
                 @click="handleCopyValue(item.value)">
              </i>
            </div>
          </li>
        </template>
        <template v-else>
          <!-- 节点基本信息 -->
          <li class="node-info"
              v-for="item in nodeInfo.filter(item =>
                !['bk_bak_operato', 'operator'].includes(item.id) || data.bkObjId === 'module'
              )"
              :key="item.id">
            <span class="node-info-title">{{ `${item.title}:`}}</span>
            <div class="node-info-content">
              <span v-if="Array.isArray(item.value)">{{ item.value.join(',') || '--' }}</span>
              <span v-else>{{ item.value || '--' }}</span>
              <i v-bk-tooltips="$t('查看详情')"
                 class="ml5 icon-monitor icon-mc-link"
                 v-if="item.link && item.value"
                 @click="handleToCmdbHost">
              </i>
              <i v-bk-tooltips="$t('点击复制')"
                 class="ml5 icon-monitor icon-mc-copy"
                 v-if="item.copy && item.value"
                 @click="handleCopyValue(item.value)">
              </i>
            </div>
          </li>
        </template>
        <!-- 主机告警信息 -->
        <li class="host-alarm">
          <div class="alarm-info-panel">
            <div :class="[
                   'count',
                   { 'active': alarmInfo.alarm_count > 0 }
                 ]"
                 @click="handleToEventCenter">
              {{alarmInfo.alarm_count}}
            </div>
            <div class="desc"> {{ $t('未恢复告警') }} </div>
          </div>
          <div class="alarm-info-panel">
            <div :class="[
                   'count',
                   { 'active': alarmInfo.alarm_strategy.enabled > 0
                     || alarmInfo.alarm_strategy.disabled > 0 }
                 ]"
                 @click="handleToStrategyConfig">
              <span>
                {{alarmInfo.alarm_strategy.enabled}}
              </span>
              <span class="disabled-count">
                /{{alarmInfo.alarm_strategy.disabled}}
              </span>
            </div>
            <div class="desc"> {{ $t('启停告警策略') }} </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Model, Emit, Prop, Watch } from 'vue-property-decorator'
import { IHostInfo } from '../performance-type'
import PerformanceModule, { ICurNode } from '../../../store/modules/performance'
import { copyText } from '../../../../monitor-common/utils/utils.js'
import MonitorVue from '../../../types/index'
import moment from 'moment'

@Component({ name: 'host-detail' })
export default class HostDetail extends Vue<MonitorVue> {
  @Prop({ default: () => ({}), type: Object }) data: ICurNode
  // 是否显示面板
  @Model('visible-change', { default: true }) readonly visible: boolean

  private isLoading = false
  // 主机信息
  private hostInfo: IHostInfo[] = []
  // 节点信息
  private nodeInfo: IHostInfo[] = []
  // 告警信息
  private alarmInfo = {
    alarm_count: 0,
    alarm_strategy: {
      disabled: 0,
      enabled: 0
    }
  }
  // 是否展示所有模块
  private showAllModule = false
  // 主机ID
  private hostId = ''
  // 状态Map
  private statusMap = {
    '-1': window.i18n.t('未知'),
    0: window.i18n.t('正常'),
    1: window.i18n.t('离线'),
    2: window.i18n.t('Agent未安装'),
    3: window.i18n.t('数据未上报')
  }

  @Watch('data', { immediate: true, deep: true })
  handleParamsChange(data: ICurNode, old: ICurNode) {
    if (!old || (data.id !== old.id)) {
      this.getDetailData()
    }
  }

  created() {
    this.hostInfo = [
      {
        id: 'bk_host_name',
        title: this.$t('主机名'),
        value: '',
        copy: true
      },
      {
        id: 'bk_host_innerip',
        title: this.$t('内网IP'),
        value: '',
        copy: true,
        link: true
      },
      {
        id: 'bk_host_outerip',
        title: this.$t('外网IP'),
        value: '',
        copy: true
      },
      {
        id: 'bk_biz_name',
        title: this.$t('所属业务'),
        value: ''
      },
      {
        id: 'bk_state',
        title: this.$t('主机运营'),
        value: ''
      },
      {
        id: 'status',
        title: this.$t('采集状态'),
        value: ''
      },
      {
        id: 'bk_os_name',
        title: this.$t('OS名称'),
        value: ''
      },
      {
        id: 'bk_cloud_name',
        title: this.$t('云区域'),
        value: ''
      },
      {
        id: 'module',
        title: this.$t('所属模块'),
        value: ''
      }
    ]
    this.nodeInfo = [
      {
        id: 'bk_inst_id',
        title: this.$t('ID'),
        value: ''
      },
      {
        id: 'bk_obj_name',
        title: this.$t('节点类型'),
        value: ''
      },
      {
        id: 'bk_inst_name',
        title: this.$t('节点名称'),
        value: ''
      },
      {
        id: 'child_count',
        title: this.$t('子级数量'),
        value: ''
      },
      {
        id: 'host_count',
        title: this.$t('主机数量'),
        value: ''
      },
      {
        id: 'operator',
        title: this.$t('主要维护人'),
        value: []
      },
      {
        id: 'bk_bak_operato',
        title: this.$t('备份维护人'),
        value: []
      }
    ]
  }

  @Emit('visible-change')
  handleTogglePanel() {
    return !this.visible
  }
  // 跳转事件中心
  handleToEventCenter() {
    if (this.alarmInfo.alarm_count > 0) {
      const endTime = moment().format('YYYY-MM-DD HH:mm:ss')
      const beginTime = moment(endTime).add(-7, 'd')
        .format('YYYY-MM-DD HH:mm:ss')
      this.$router.push({
        name: 'event-center',
        params: {
          query: this.data.ip, // 自定义ip搜索条件
          status: 'ABNORMAL',
          beginTime,
          endTime
        }
      })
    }
  }
  // 跳转策略
  handleToStrategyConfig() {
    const { alarm_strategy } = this.alarmInfo
    if (alarm_strategy.enabled > 0 || alarm_strategy.disabled > 0) {
      this.$router.push({
        name: 'strategy-config',
        params: {
          ip: this.data.ip,
          bkCloudId: this.data.cloudId
        }
      })
    }
  }

  async getDetailData() {
    this.isLoading = true
    let detailData: any = {}
    let configData = []
    if (this.data.type === 'host' && this.data.ip) {
      this.showAllModule = false
      detailData = await PerformanceModule.getHostDetail({
        ip: this.data.ip,
        bk_cloud_id: this.data.cloudId
      })
      configData = this.hostInfo
      this.hostId = detailData.bk_host_id
    } else if (this.data.type === 'node' && this.data.bkInstId) {
      detailData = await PerformanceModule.getNodeDetail({
        bk_obj_id: this.data.bkObjId,
        bk_inst_id: this.data.bkInstId
      })
      configData = this.nodeInfo
    }

    // 基本信息
    Object.keys(detailData).forEach((key) => {
      const item = configData.find(item =>  item.id === key)
      item && (item.value = detailData[key])
    })
    // 告警信息
    this.alarmInfo.alarm_count = detailData.alarm_count || 0
    this.alarmInfo.alarm_strategy = detailData.alarm_strategy || {}
    this.$store.commit('app/SET_NAV_TITLE', this.data.type === 'host'
      ? detailData.bk_host_innerip : detailData.bk_inst_name)
    this.isLoading = false
  }

  handleToggleModule() {
    this.showAllModule = !this.showAllModule
  }

  handleToCmdbHost() {
    window.open(`${this.$store.getters.cmdbUrl}/#/resource/host/${this.hostId}`, '_blank')
  }

  handleCopyValue(value) {
    copyText(value)
    this.$bkMessage({
      theme: 'success',
      message: this.$t('复制成功')
    })
  }
}
</script>
<style lang="scss" scoped>
.host-detail {
  display: flex;
  flex-direction: column;
  border-left: 1px solid #f0f1f5;
  &-title {
    display: flex;
    align-items: center;
    flex: 0 0 42px;
    border-bottom: 1px solid #f0f1f5;
    i {
      transform: rotate(90deg);
      font-size: 24px;
      color: #979ba5;
      cursor: pointer;
      margin-left: 2px;
    }
    span {
      margin-left: 4px;
    }
  }
  &-content {
    padding: 15px 24px 0 16px;
    overflow: auto;
    .host-info {
      display: flex;
      line-height: 20px;
      margin-bottom: 10px;
      &-title {
        flex: 0 0 60px;
        text-align: left;
        color: #979ba5;
      }
      &-content {
        flex: 1;
        .status-normal {
          color: #2dcb56;
        }
        .status-unkown {
          color: #ea3636;
        }
        .module-expand {
          height: 40px;
          overflow: hidden;
        }
        .module-item {
          line-height: 20px;
          margin: 0;
        }
        .btn {
          font-size: 12px;
        }
        i {
          cursor: pointer;
        }
        .icon-mc-copy {
          font-size: 14px;
          color: #3a84ff;
        }
        .icon-mc-link {
          color: #3a84ff;
        }
      }
    }
    .node-info {
      display: flex;
      line-height: 20px;
      margin-bottom: 10px;
      &-title {
        flex: 0 0 80px;
        text-align: left;
        color: #979ba5;
      }
      &-content {
        flex: 1;
        .status-normal {
          color: #2dcb56;
        }
        .status-unkown {
          color: #ea3636;
        }
        .module-expand {
          height: 40px;
          overflow: hidden;
        }
        .module-item {
          line-height: 20px;
          margin: 0;
        }
        .btn {
          font-size: 12px;
        }
        i {
          cursor: pointer;
        }
        .icon-mc-copy {
          font-size: 14px;
          color: #3a84ff;
        }
        .icon-mc-link {
          color: #3a84ff;
        }
      }
    }
    .host-alarm {
      display: flex;
      .alarm-info-panel {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        flex: 1;
        height: 64px;
        border-radius: 2px;
        background: #f5f6fa;
        &:hover {
          background: #3a84ff;
          & span:nth-of-type(1),
          & .count.active {
            color: #ffff;
          }
          & span:nth-of-type(2),
          & .desc {
            color: #a3c5fd;
          }
        }
        &:last-child {
          margin-left: 2px;
        }
        .count {
          font-size: 16px;
          color: #979ba5;
          line-height: 26px;
          &.active {
            color: #000;
            cursor: pointer;
          }
          .disabled-count {
            color: #979ba5;
          }
        }
        .desc {
          color: #979ba5;
          line-height: 20px;
        }
      }
    }
  }
}
</style>
