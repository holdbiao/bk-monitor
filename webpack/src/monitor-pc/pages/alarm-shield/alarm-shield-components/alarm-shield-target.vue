<template>
  <div class="alarm-shield-target" :class="{ 'out-line': loading }" v-bkloading="{ 'isLoading': loading }">
    <!-- 编辑时不能修改屏蔽目标 -->
    <template v-if="!isEdit">
      <!-- 不同选择器btn -->
      <div class="bk-button-group">
        <bk-button v-for="(item, index) in buttonList" :key="index" class="btn-width"
                   :class="{ 'is-selected': targetType === item.id }" @click.stop="handleBtnChange(item.id)">
          {{ item.name }}
        </bk-button>
      </div>
      <!-- 各种选择器的提示 -->
      <div class="tips-text"><i class="icon-monitor icon-tips item-icon"></i>{{ tips[targetType] }}</div>
      <!-- 3种选择器  实例  IP  节点 -->
      <div class="target-selector" v-for="item in topoSelector" :key="item.type">
        <topo-selector v-show="item.type === targetType"
                       :ref="item.ref"
                       :class="item.className"
                       :instance-type="item.instanceType"
                       :is-instance="item.isInstance"
                       min-width="836"
                       :default-active="item.defaultActive"
                       :topo-height="item.type === 'ip' ? 360 : 400"
                       @table-data-change="handleSelectTableData"
                       @loading-change="handleLoadingChange(arguments, item.type)">
          <!-- 实例 -->
          <template v-if="item.type === 'instance'" #static-ip-panel="staticTableData">
            <bk-table :data="staticTableData.data" :class="{ 'hide-last-td': targetType !== 'biz' && curMetricItem.tableData.length > 9 }">
              <bk-table-column :label="$t('实例名称')" prop="name" width="516"></bk-table-column>
              <bk-table-column :label="$t('操作')" align="center" width="80">
                <template slot-scope="scope">
                  <bk-button text @click="handleDeleteTarget(scope.row, scope.$index)"> {{ $t('移除') }} </bk-button>
                </template>
              </bk-table-column>
            </bk-table>
          </template>
          <!-- IP -->
          <template v-else-if="item.type === 'ip'" #static-ip-panel="staticTableData">
            <bk-table :data="staticTableData.data">
              <bk-table-column label="IP" prop="ip"></bk-table-column>
              <bk-table-column :label="$t('操作')" align="center" width="80">
                <template slot-scope="scope">
                  <bk-button text @click="handleDeleteTarget(scope.row, scope.$index)"> {{ $t('移除') }} </bk-button>
                </template>
              </bk-table-column>
            </bk-table>
          </template>
          <!-- 节点 -->
          <template v-eles-if="item.type === 'node'" #dynamic-topo-panel="dynamicTopoTableData">
            <bk-table :data="dynamicTopoTableData.data"
                      :height="460"
                      :max-height="460">
              <bk-table-column :label="$t('节点名称')"
                               prop="name"></bk-table-column>
              <bk-table-column :label="$t('操作')" align="center" width="80">
                <template slot-scope="scope">
                  <bk-button text @click="handleDeleteTarget(scope.row, scope.$index)"> {{ $t('移除') }} </bk-button>
                </template>
              </bk-table-column>
            </bk-table>
          </template>
        </topo-selector>
      </div>
    </template>
    <!-- 编辑勾选展示 -->
    <bk-table class="static-table" v-else-if="targetType !== 'biz' && isEdit" :data="targetData" :max-height="450">
      <bk-table-column :label="labelMap[type]" prop="name"></bk-table-column>
    </bk-table>
    <span v-if="targetError" class="target-empty-msg"> {{ $t('请选择屏蔽目标') }} </span>
  </div>
</template>

<script lang="ts">
import { Component, Vue, Prop } from 'vue-property-decorator'
import TopoSelector from '../../collector-config/collector-add/config-select/topo-selector.vue'
import { TranslateResult } from 'vue-i18n/types/index'
interface ISelector {
  type: string,
  loading: boolean,
  tableData: any[],
  isInstance: boolean,
  defaultActive: number,
  instanceType: string,
  className: string,
  ref: string
}
@Component({
  components: {
    TopoSelector
  }
})
export default class AlarmShieldTarget extends Vue {
  loading = false
  targetError = false //  未勾选提示
  targetType = 'ip' //  当前选择器类型
  instanceType = '' //
  topoSelector: ISelector[] = [
    {
      type: 'instance', //  ip选择器类型
      loading: false, //
      tableData: [],
      isInstance: true,
      defaultActive: 1,
      instanceType: 'service',
      className: 'instance-selector', //  每种选择器对应的class名称
      ref: 'instance' //  选择器的
    },
    {
      type: 'ip',
      loading: false,
      tableData: [],
      isInstance: false,
      defaultActive: 0,
      instanceType: '',
      className: 'only-ip',
      ref: 'ip'
    },
    {
      type: 'node',
      loading: false,
      tableData: [],
      isInstance: false,
      defaultActive: 2,
      instanceType: '',
      className: 'instance-selector',
      ref: 'node'
    }
  ]

  //  选择器类型btn
  btnList: { name: TranslateResult; id: string }[] = []
  //  不同选择器提示语
  tips: { instance: TranslateResult; ip: TranslateResult; node: TranslateResult, biz: TranslateResult }
  //  不同类型的展示标签
  labelMap: { ip: TranslateResult, instance: TranslateResult, node: TranslateResult, biz: TranslateResult }
  //  勾选的屏蔽数据
  tableData: any[] = []

  //  是否编辑
  @Prop({ default: false })
  isEdit: boolean

  //  targetData回填数据
  @Prop({ default: () => ([]) })
  targetData: []

  //  targetType
  @Prop()
  type: string

  @Prop({ default: () => ([]) })
  dataTarget: string[]

  //  当前选择器数据
  get curMetricItem(): ISelector {
    return this.topoSelector.find(item => item.type === this.targetType)
  }

  get buttonList() {
    const res = [{ name: this.$t('节点'), id: 'node', order: 2 }]
    if (this.dataTarget.find(item => item === 'HOST')) {
      res.push({ name: this.$t('主机'), id: 'ip', order: 1 })
    }
    if (this.dataTarget.find(item => item === 'SERVICE')) {
      res.push({ name: this.$t('服务实例'), id: 'instance', order: 0 })
    }
    return res.sort((a, b) => a.order - b.order)
  }

  created() {
    this.tips = {
      instance: this.$t('服务实例屏蔽: 屏蔽告警中包含该实例的通知'),
      ip: this.$t('主机屏蔽: 屏蔽告警中包含该IP通知,包含对应的实例'),
      node: this.$t('节点屏蔽: 屏蔽告警中包含该节点下的所有IP和实例的通知'),
      biz: this.$t('业务屏蔽: 屏蔽告警中包含该业务的所有通知')
    }
    this.labelMap = {
      ip: this.$t('主机'),
      instance: this.$t('服务实例'),
      node: this.$t('节点名称'),
      biz: this.$t('业务')
    }
  }

  //  选择器切换
  handleBtnChange(id: string): void {
    this.targetType = id
    this.instanceType = id === 'instance' ? 'service' : ''
    this.loading = this.curMetricItem.loading
    this.targetError = false
  }

  //  勾选的数据放到对应tableData中
  handleSelectTableData(tableData: []): void {
    this.targetError = !tableData.length
    this.curMetricItem.tableData = tableData
  }

  //  切换选择器loading变化
  handleLoadingChange(loadingStatus: boolean[], type: string): void {
    const [loadingStatusItem] = loadingStatus
    if (this.targetType === type) {
      this.loading = loadingStatusItem
    }
    this.curMetricItem.loading = loadingStatusItem
  }

  //  emit
  getTargetData(): {'scope_type': string, target: []} {
    const data = this.curMetricItem.tableData
    const { type } = this.curMetricItem
    const target: {
      ip: {ip: string, 'bk_cloud_id': string}[],
      node: {'bk_obj_id': string, 'bk_inst_id': string}[],
      instance: {'service_instance_id': string}[]
    } = {
      ip: type === 'ip' ? data.map(item => ({ ip: item.ip, bk_cloud_id: item.bkCloudId })) : [],
      node: type === 'node' ? data.map(item => ({ bk_obj_id: item.bkObjId, bk_inst_id: item.bkInstId })) : [],
      instance: type === 'instance' ? data.map(item => item.service_instance_id) : []
    }
    return { scope_type: type, target: target[type] }
  }

  //  删除已勾选表格数据
  handleDeleteTarget(row: any, index: number): void {
    if (this.targetType === 'node') {
      this.$refs[this.curMetricItem.ref][0].handleDeleteDynamicTopo(row, index)
    } else {
      this.$refs[this.curMetricItem.ref][0].handleDeleteStaticIp(row, index)
    }
  }
}
</script>

<style lang="scss" scoped>
    .alarm-shield-target {
      position: relative;
      &.out-line {
        outline: 1px solid #dcdee5;
      }
      .btn-width {
        width: 168px;
      }
      .tips-text {
        display: flex;
        align-items: center;
        font-size: 12px;
        margin: 10px 0;
        .item-icon {
          margin-right: 6px;
          font-size: 14px;
          line-height: 1;
          color: #979ba5;
        }
      }
      .target-selector {
        display: block;
        .topo-selector {
          /deep/ .left-tab {
            display: none;
          }
          /deep/ .bk-big-tree {
            height: 365px;
            overflow: auto;
          }
        }
        /deep/ .left-content-wrap {
          height: calc(var(--height) - 95px);
        }
        .hide-last-td-border {
          border-bottom: 0;
          .bk-table-body-wrapper {
            tr:last-child {
              display: none;
            }
          }
        }
        .instance-selector {
          /deep/ .left-tab {
            display: none;
          }
          /deep/ .bk-big-tree {
            height: 400px;
            overflow: auto;
          }
          /deep/ .left-content {
            padding-top: 17px;
          }
          /deep/ .left-content-select {
            display: none;
          }
          /deep/ .left-content-wrap {
            height: calc(var(--height) - 59px);
          }
          /deep/ .dynamic-topo {
            margin-top: 0;
            padding-top: 0;
          }
          /deep/ .right-panel-title {
            display: none;
          }
          /deep/ .right-wrap.is-expand {
            border-top: 0;
          }
          /deep/ .ip-select-right {
            border-top: 1px solid #dcdee5;
            border-bottom: 1px solid #dcdee5;
            overflow: hidden;
            background-image: linear-gradient(
              180deg,
              #fff 1px,
              rgba(0, 0, 0, 0) 1px,
              rgba(0, 0, 0, 0) 100%
            ),
              linear-gradient(
              -90deg,
              #dcdee5 1px,
              rgba(0, 0, 0, 0) 1px,
              rgba(0, 0, 0, 0) 100%
            ),
              linear-gradient(
              0deg,
              #fff 1px,
              rgba(0, 0, 0, 0) 1px,
              rgba(0, 0, 0, 0) 100%
            );
            .bk-table-body-wrapper {
              overflow-y: auto;
              height: 417px;
            }
          }
        }
        /deep/ .static-topo {
          margin-top: 0;
          margin-bottom: 0;
          padding-top: 0;
        }
      }
      .target-empty-msg {
        position: absolute;
        left: 0;
        bottom: -19px;
        font-size: 12px;
        color: #ea3636;
      }
      .static-table {
        width: 836px;
        /deep/ .cell {
          padding-left: 30px;
        }
        &:before {
          height: 1px;
        }
      }
    }
    .only-ip {
      /deep/ .right-empty {
        margin-top: 165px;
      }
    }
</style>
