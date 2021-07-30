<template>
  <div class="data-query-conditions">
    <!-- ip选择器 -->
    <div class="ip-select-wrapper">
      <span class="label" v-show="queryData.target.length">{{ `${$t('监控目标')} :` }}&nbsp;</span>
      <span class="handle" @click="handleTarget"> {{ targetDes }}</span>
      <strategy-set-target
        v-if="target.show"
        :biz-id="bizId"
        :can-save-empty="true"
        :dialog-show.sync="target.show"
        :target-type="target.targetType"
        :object-type="target.objectType"
        :target-list="queryData.target"
        @target-type-change="handleTargetTypeChange"
        @targets-change="handleTargetChange">
      </strategy-set-target>
    </div>
    <!-- 查询条件 -->
    <data-query-conditions-item
      v-for="(item, index) in queryData.queryConfigs"
      :key="item.key"
      :index="index"
      :data="item">
    </data-query-conditions-item>
    <!-- 添加查询条件 -->
    <div class="add-search-conditions">
      <i class="icon-monitor icon-mc-add"></i>
      <span class="add-btn" @click="addQueryConditions">{{ $t('添加查询条件') }}</span>
    </div>
    <!-- 操作按钮组 -->
    <div class="handle-btn-group">
      <bk-button theme="primary" class="btn" @click="handleQuery" :disabled="canBeQuery">{{ $t('查询') }}</bk-button>
      <bk-button class="btn" @click="saveQuery" :disabled="!queryData.queryConfigs.length">{{ $t('保存查询') }}</bk-button>
      <bk-button class="btn" :disabled="canBeEmptied" @click="handleClearQueryConfig">{{ $t('清空') }}</bk-button>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Watch } from 'vue-property-decorator'
import DataQueryConditionsItem from './data-query-conditions-item.vue'
import MonitorVue from '../../../types/index'
import StrategySetTarget from '../../strategy-config/strategy-config-set/strategy-set-target/strategy-set-target.vue'
import DataRetrieval from '../../../store/modules/data-retrieval'

@Component({
  name: 'data-query-conditions',
  components: {
    DataQueryConditionsItem,
    StrategySetTarget
  }
})
export default class DataQueryConditions extends Vue<MonitorVue> {
  // 查询条件展开状态
  isShowContent = true

  showTarget = false
  target = {
    show: false,
    objectType: 'HOST',
    targetType: 'INSTANCE'
  }
  // 查询数据
  get queryData() {
    return DataRetrieval.queryDataGetter
  }

  get bizId() {
    return this.$store.getters.bizId
  }

  // 监控目标描述
  get targetDes(): string {
    const { target = [] } = this.queryData
    const cloneTarget = JSON.parse(JSON.stringify(target))
    const nameList = this.mainlineObjectTopoList
    let targetDes = this.$tc('点击选择监控目标')
    if (!cloneTarget.length) return targetDes
    // 动态选择目标
    if ('bk_obj_id' in cloneTarget[0]) {
      let list = cloneTarget.map((item) => {
        item.name = nameList.find(set => set.bk_obj_id === item.bk_obj_id).bk_obj_name
        return item
      })
      // 统计数量
      list = list.map((item) => {
        const count = list.reduce((pre, set) => {
          if (item.bk_obj_id === set.bk_obj_id) pre += 1
          return pre
        }, 0)
        item.count = count
        return item
      })
      // 去重
      const temp = []
      list = list.map((item) => {
        if (!temp.includes(item.name)) {
          temp.push(item.name)
          return {
            name: item.name,
            count: item.count
          }
        }
        return null
      }).filter(item => item)
      const str = list.map(item => `${item.count} ${item.name}`).join('、')
      targetDes = `${this.$tc('已选择')} ${str}`
    } else { // 静态目标
      targetDes = `${this.$tc('已选择')} ${cloneTarget.length} ${this.$tc('主机单位')}${this.$tc('主机')}`
    }
    return targetDes
  }

  get mainlineObjectTopoList() {
    return DataRetrieval.mainlineObjectTopoGetter
  }

  get canBeEmptied() {
    let flag = false
    flag = this.queryData.queryConfigs.some(item => item.metricField)
    return !(!!this.queryData.target.length || flag)
  }

  readonly canBeQuery = false;

  @Watch('queryData.targetType', { immediate: true })
  watchTargetType(v) {
    this.target.targetType = v
  }

  //   created() {
  //     DataRetrieval.handleAddCondition()
  //   }

  // 保存查询条件
  saveQuery() {
    this.$bus.$emit('get-conditions-value')
    DataRetrieval.addQueryHistory()
  }

  // 新增查询条件
  addQueryConditions() {
    DataRetrieval.handleAddCondition()
  }

  // 目标主机
  handleTargetChange(value) {
    DataRetrieval.setData({ expr: 'queryData.target', value })
  }

  handleTargetTypeChange(type) {
    this.target.targetType = type
    DataRetrieval.setData({ expr: 'queryData.targetType', value: type })
  }

  // 显示目标弹窗
  handleTarget() {
    this.target.show = true
  }

  // 查询
  handleQuery() {
    DataRetrieval.handleQuery()
  }

  // 清空查询配置
  handleClearQueryConfig() {
    const mapList = [
      { expr: 'queryData.queryConfigs', value: [] },
      { expr: 'queryConfigsResult', value: {} },
      { expr: 'queryData.target', value: [] }
    ]
    DataRetrieval.setDataList(mapList)
    DataRetrieval.handleAddCondition()
  }
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.data-query-conditions {
  .ip-select-wrapper {
    display: flex;
    align-items: center;
    height: 40px;
    padding: 0 20px 0 44px;
    box-sizing: border-box;
    border-bottom: 1px solid #f0f1f5;
    font-size: 12px;
    line-height: 20px;
    .label {
      flex-shrink: 0;
      color: #313238;
    }
    .handle {
      color: $primaryFontColor;
      cursor: pointer;

      @include ellipsis;
    }
  }
  .conditions-item {
    font-size: 12px;
    border-bottom: 1px solid #f0f1f5;
    .icon-arrow-down {
      display: inline-block;
      width: 24px;
      height: 24px;
      font-size: 28px;
      &::before {
        width: 100%;
        height: 100%;
        transform: rotate(0deg);
        transition: all .3s ease-in-out;

        @include content-center;
      }
    }
    .arrow-right {
      &::before {
        transform: rotate(-90deg);
      }
    }
    .item-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 20px 8px 14px;
      cursor: pointer;
      .header-left {
        display: flex;
        align-items: center;
        .title {
          margin-left: 6px;
          color: #313238;
        }
      }
    }
    .item-content {
      padding: 0 20px 0 44px;
      overflow: hidden;
      transition: height .3s ease-in-out;
      .form-item {
        padding-bottom: 15px;
      }
      .group {
        display: flex;
        .group-item {
          width: 50%;
          &:not(:last-child) {
            margin-right: 8px;
          }
        }
      }
      .label {
        line-height: 20px;
        color: $defaultFontColor;
        margin-bottom: 6px;
      }
    }
  }
  .add-search-conditions {
    display: flex;
    align-items: center;
    height: 40px;
    padding: 0 20px 0 14px;
    border-bottom: 1px solid #f0f1f5;
    .icon-mc-add {
      width: 24px;
      height: 24px;
      font-size: 24px;
      color: $primaryFontColor;
      cursor: pointer;
      overflow: hidden;

      @include content-center;
      &::before {
        @include content-center;
      }
    }
    .add-btn {
      margin-left: 6px;
      color: $primaryFontColor;
      cursor: pointer;
    }
  }
  .handle-btn-group {
    padding: 16px 20px;
    font-size: 0;
    .btn {
      &:not(:last-child) {
        margin-right: 8px;
      }
    }
  }
}
</style>
