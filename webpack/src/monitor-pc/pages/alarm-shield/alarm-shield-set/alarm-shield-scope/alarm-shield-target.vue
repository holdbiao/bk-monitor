<template>
  <div class="alarm-shield-target">
    <div class="topo-selector-container" :class="{ 'out-line': loading }" v-bkloading="{ 'isLoading': loading }">
      <div v-show="targetType === 'instance'">
        <topo-selector
          ref="instance"
          class="instance-selector"
          instance-type="service"
          :is-instance="true"
          min-width="836"
          :default-active="1"
          :topo-height="400"
          @table-data-change="handleSelectTableData"
          @loading-change="handleLoadingChange(arguments, 'instance')">
          <template v-slot:static-ip-panel="staticTableData">
            <bk-table
              :height="460"
              :max-height="460"
              :data="staticTableData.data"
              :class="{ 'hide-last-td': targetType !== 'biz' && topoSelector[targetType].tableData.length > 9 }">
              <bk-table-column :label="$t('实例名称')" prop="name">
              </bk-table-column>
              <bk-table-column :label="$t('操作')" align="center" width="80">
                <template slot-scope="scope">
                  <bk-button text @click="handleDeleteTarget(scope.row, scope.$index)"> {{ $t('移除') }} </bk-button>
                </template>
              </bk-table-column>
            </bk-table>
          </template>
        </topo-selector>
      </div>
      <div v-show="targetType === 'ip'">
        <topo-selector
          class="only-ip"
          ref="ip"
          :default-active="0"
          min-width="836"
          :is-instance="false"
          :topo-height="360"
          @table-data-change="handleSelectTableData"
          @loading-change="handleLoadingChange(arguments, 'ip')">
          <template v-slot:static-ip-panel="staticTableData">
            <bk-table :data="staticTableData.data">
              <bk-table-column label="IP" prop="ip"></bk-table-column>
              <bk-table-column :label="$t('操作')" align="center" width="80">
                <template slot-scope="scope">
                  <bk-button text @click="handleDeleteTarget(scope.row, scope.$index)"> {{ $t('移除') }} </bk-button>
                </template>
              </bk-table-column>
            </bk-table>
          </template>
        </topo-selector>
      </div>
      <div v-show="targetType === 'node'">
        <topo-selector
          ref="node"
          class="instance-selector"
          :default-active="2"
          min-width="836"
          :is-instance="false"
          :topo-height="400"
          @table-data-change="handleSelectTableData"
          @loading-change="handleLoadingChange(arguments, 'node')">
          <template v-slot:dynamic-topo-panel="dynamicTopoTableData">
            <bk-table
              :height="460"
              :max-height="460"
              :data="dynamicTopoTableData.data">
              <bk-table-column :label="$t('节点名称')" prop="name"></bk-table-column>
              <bk-table-column :label="$t('操作')" align="center" width="80">
                <template slot-scope="scope">
                  <bk-button text @click="handleDeleteTarget(scope.row, scope.$index)"> {{ $t('移除') }} </bk-button>
                </template>
              </bk-table-column>
            </bk-table>
          </template>
        </topo-selector>
      </div>
      <span v-if="targetError" class="target-empty-msg"> {{ $t('请选择屏蔽目标') }} </span>
    </div>
  </div>
</template>
<script>
import TopoSelector from '../../../collector-config/collector-add/config-select/topo-selector'
export default {
  name: 'alarm-shield-target',
  components: {
    TopoSelector
  },
  props: {
    targetType: {
      type: String,
      default: 'instance'
    }
  },
  data() {
    return {
      loading: false,
      targetError: false,
      topoSelector: {
        instance: {
          load: true,
          checkedData: [],
          tableData: []
        },
        ip: {
          load: false,
          checkedData: [],
          tableData: []
        },
        node: {
          load: true,
          checkedData: [],
          tableData: []
        }
      }
    }
  },
  watch: {
    targetType(v) {
      if (v === 'biz') return
      this.loading = this.topoSelector[v].load
      this.targetError = false
    }
  },
  methods: {
    handleSelectTableData(v) {
      this.targetError = !v.length
      this.topoSelector[this.targetType].tableData = v
    },
    handleLoadingChange(arg, type) {
      const [argItem] = arg
      if (this.targetType === type) {
        this.loading = argItem
      }
      this.topoSelector[type].load = argItem
    },
    handleGetTarget() {
      const data = this.$refs[this.targetType].getCheckedData()
      if (!data.length) {
        this.targetError = true
        return false
      }
      return data
    },
    handleDeleteTarget(row, index) {
      if (this.targetType === 'node') {
        this.$refs[this.targetType].handleDeleteDynamicTopo(row, index)
      } else {
        this.$refs[this.targetType].handleDeleteStaticIp(row, index)
      }
    }
  }

}
</script>
<style lang="scss" scoped>
.alarm-shield-target {
  .topo-selector-container {
    position: relative;
    &.out-line {
      outline: 1px solid #dcdee5;
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
    .topo-selector {
      /deep/ .left-tab {
        display: none;
      }
      /deep/ .bk-big-tree {
        height: 365px;
        overflow: auto;
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
        background-image: linear-gradient(180deg, #fff 1px, rgba(0, 0, 0, 0) 1px, rgba(0, 0, 0, 0) 100%), linear-gradient(-90deg, #dcdee5 1px, rgba(0, 0, 0, 0) 1px, rgba(0, 0, 0, 0) 100%), linear-gradient(0deg, #fff 1px, rgba(0, 0, 0, 0) 1px, rgba(0, 0, 0, 0) 100%);
      }
    }
    /deep/ .static-topo {
      margin-top: 0;
      margin-bottom: 0;
      padding-top: 0;
    }
    .target-empty-msg {
      position: absolute;
      left: 0;
      bottom: -19px;
      font-size: 12px;
      color: #ea3636;
    }
  }
  .only-ip {
    /deep/ .right-empty {
      margin-top: 165px;
    }
  }
}
</style>
