<template>
  <div class="detail-target">
    <div class="right-wrapper" v-if="left.active !== -1 && strategyList.length">
      <!-- 监控详情 -->
      <div class="right-form">
        <div class="right-form-title">{{ strategyData.name || strategyData.metricField }} <span class="title-desc" v-if="strategyData.descVisible">（{{ strategyData.metricDescription }}）</span> <i v-if="strategyData.remarks && strategyData.remarks.length" class="icon-monitor icon-tips set-desc" @click="strategyData.descVisible = !strategyData.descVisible"></i></div>
        <template v-if="strategyData.remarks && strategyData.remarks.length">
          <strategy-custom-desc :desc-list="strategyData.remarks" v-model="strategyData.descVisible"></strategy-custom-desc>
        </template>
        <template v-if="!(strategyData.dataTypeLabel === 'event' && strategyData.dataSourceLabel === 'bk_monitor')">
          <!-- 日志 -->
          <template v-if="strategyData.dataTypeLabel === 'log' && strategyData.dataSourceLabel !== 'bk_monitor'">
            <!-- <div class="right-form-item">
                            <div class="item-label"> {{ $t('索引集') }} </div>
                            <div class="item-center">{{ strategyData.metricField }}</div>
                        </div> -->
            <div class="right-form-item">
              <div class="item-label"> {{ $t('检索语句') }} </div><div class="item-center">{{ strategyData.keywordsQueryString }}</div>
            </div>
          </template>
          <template>
            <div class="right-form-item">
              <div class="item-label"> {{ $t('计算公式') }} </div>
              <!-- 实时 -->
              <div class="item-center">
                <div v-if="strategyData.aggMethod === 'REAL_TIME'"> {{ $t('实时') }} </div>
                <div v-else>{{ strategyData.aggMethod && strategyData.aggMethod.toLocaleUpperCase() }}</div>
              </div>
            </div>
            <div class="right-form-item" v-if="strategyData.aggMethod !== 'REAL_TIME'">
              <div class="item-label"> {{ $t('监控周期') }} </div><div>{{ strategyData.aggInterval / 60 }} {{ $t('分钟') }} </div>
            </div>
            <div class="right-form-item" v-if="strategyData.aggMethod !== 'REAL_TIME'">
              <div class="item-label"> {{ $t('监控维度') }} </div>
              <div class="item-agg-condition">
                <template>
                  <div class="item-agg-dimension mb-2" v-for="(item, index) in aggDimension" :key="index">{{item}}</div>
                </template>
              </div>
            </div>
            <div class="right-form-item">
              <div class="item-label"> {{ $t('监控条件') }} </div>
              <div class="item-agg-condition">
                <div class="item-agg-dimension mb-2" v-for="(item, index) in aggCondition" :key="index" :style="{ 'color': aggConditionColorMap[item], 'font-weight': aggConditionFontMap[item] }">
                  {{Array.isArray(item) ? item.join(' , ') : item }}
                </div>
              </div>
            </div>
          </template>
          <template>
            <div class="right-form-item" v-if="target && target.target && target.target.length">
              <div class="item-label"> {{ $t('监控目标') }} </div>
              <div class="item-center">
                {{targetMessage.title}} <span style="color: #979ba5">{{targetMessage.subTitle}}</span><span @click="handleShowTarget" class="item-target-btn">{{ $t('查看目标') }}</span>
              </div>
            </div>
          </template>
          <!-- 算法 -->
          <template v-if="!(strategyData.dataTypeLabel === 'event' && strategyData.dataTypeLabel === 'bk_monitor')">
            <div class="right-form-item">
              <div class="item-label need-position"> {{ $t('检测算法') }} </div>
              <div class="item-center item-position">
                <template v-for="item in detectAlgorithmList">
                  <target-right-panel
                    v-if="item.list && item.list.length"
                    :key="item.level"
                    :level-name="item.name"
                    :level="item.level"
                    :algorithm-list="item.list">
                  </target-right-panel>
                </template>
              </div>
            </div>
          </template>
        </template>
        <!-- 操作系统-事件 -->
        <template v-else>
          <!-- 操作系统-自定义事件 -->
          <div class="right-form-item">
            <div class="item-label"> {{ $t('告警级别') }} </div>
            <bk-radio-group v-model="eventLevel">
              <bk-radio class="item-radio" :disabled="true" :value="1"> {{ $t('致命') }} </bk-radio>
              <bk-radio class="item-radio" :disabled="true" :value="2"> {{ $t('预警') }} </bk-radio>
              <bk-radio class="item-radio" :disabled="true" :value="3"> {{ $t('提醒') }} </bk-radio>
            </bk-radio-group>
          </div>
          <div class="right-form-item">
            <div class="item-label"> {{ $t('监控条件') }} </div>
            <div class="item-agg-condition">
              <div class="item-agg-dimension mb-2" v-for="(item, index) in aggCondition" :key="index" :style="{ 'color': aggConditionColorMap[item], 'font-weight': aggConditionFontMap[item] }">
                {{Array.isArray(item) ? item.join(' , ') : item }}
              </div>
            </div>
          </div>
          <template v-if="target && target.target && target.target.length">
            <div class="right-form-item">
              <div class="item-label"> {{ $t('监控目标') }} </div>
              <div class="item-center">
                {{targetMessage.title}} <span style="color: #979ba5">{{targetMessage.subTitle}}</span><span @click="handleShowTarget" class="item-target-btn">{{ $t('查看目标') }}</span>
              </div>
            </div>
          </template>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { getLogFields, getMetricList } from '../../../../monitor-api/modules/strategies'
import { strategyMapMixin } from '../../../common/mixins'
import TargetRightPanel from './target-right-panel.vue'
import StrategyCustomDesc from '../strategy-config-set/strategy-custom-desc/strategy-custom-desc'
import { createNamespacedHelpers } from 'vuex'
const { mapActions, mapGetters } = createNamespacedHelpers('strategy-config')

export default {
  name: 'StrategyConfigDetailTarget',
  components: {
    TargetRightPanel,
    StrategyCustomDesc
  },
  mixins: [strategyMapMixin],
  props: {
    // itemList
    strategyList: {
      type: Array,
      default: () => ([])
    },
    // 监控目标
    target: {
      type: Object,
      default() {
        return {}
      }
    }
  },
  data() {
    return {
      left: {
        enter: -1,
        active: 1
      },
      strategyName: [], // 左边监控指标列表
      strategyIndex: 0, // 选择的监控指标项
      strategyData: {}, // 左边对应监控的数据
      detectAlgorithmList: [], // 检测算法数据
      eventLevel: 1,
      dimensionList: new Map(), // 监控维度中文Map列表
      conditionList: new Map(), // 监控条件中文Map列表
      aggDimension: [], // 监控维度
      aggCondition: [], // 监控条件
      otherType: false,
      levelMap: [
        {
          name: this.$t('致命'),
          level: 1
        },
        {
          name: this.$t('预警'),
          level: 2
        },
        {
          name: this.$t('提醒'),
          level: 3
        }
      ],
      targetMessage: {
        title: '',
        subTitle: ''
      }
    }
  },
  computed: {
    ...mapGetters(['dimensionsValueMap'])
  },
  watch: {
    strategyList(newV) {
      if (newV.length) {
        this.handleChangeItemList(newV, 0)
      }
    },
    target(v) {
      const { target, bkTargetType, bkObjType } = v
      if (target?.length) {
        let len = target.length
        if (['TOPO', 'SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(bkTargetType)) {
          const count = target.reduce((pre, item) => {
            const allHost = item.allHost || []
            return Array.from(new Set([...pre, ...allHost]))
          }, []).length
          // 服务模板和集群模板比较特殊，不能直接取target的长度作为数量
          if (['SERVICE_TEMPLATE', 'SET_TEMPLATE'].includes(bkTargetType)) {
            const props = bkTargetType.replace('_', '')
            len = target.reduce((pre, item) => (item[props]
              ? Array.from(new Set([...pre, item[props]]))
              : pre
            ), []).length
          }
          const textMap = {
            TOPO: `${this.$t('个')}${this.$t('节点')}`,
            SERVICE_TEMPLATE: `${this.$t('个')}${this.$t('服务模板')}`,
            SET_TEMPLATE: `${this.$t('个')}${this.$t('集群模板')}`
          }
          this.targetMessage.title = `${len} ${textMap[bkTargetType]}`
          const res = bkObjType === 'SERVICE' ? `${this.$t('个')}${this.$t('实例')}` : `${this.$t('台')}${this.$t('主机')}`
          this.targetMessage.subTitle = `（ ${count} ${res}）`
        } else {
          this.targetMessage.title = `${len} ${this.$t('台主机')} `
        }
      }
    }
  },
  methods: {
    ...mapActions(['getVariableValueList']),
    // 点击查看监控目标
    handleShowTarget() {
      this.$emit('show-target', true)
    },
    // 获取监控项中文Map列表
    getDimensionList(data) {
      const parmas = {
        data_type_label: data.dataTypeLabel,
        data_source_label: data.dataSourceLabel,
        page: 1,
        page_size: 10,
        search_fields: {
          result_table_id: data.resultTableId || data.result_table_id,
          metric_field: data.metricField
        }
      }

      return getMetricList(parmas).then((res) => {
        const data = res.metric_list[0].dimensions
        data.forEach((item) => {
          this.conditionList.set(item.id, item.name)
        })
        this.$emit('dimension-list-change', this.conditionList, data)
      })
        .catch(() => [])
        .finally(() => {
          this.$emit('target-loading', false)
        })
    },
    // 日志类型中文Map列表
    getLogFields(data) {
      return getLogFields({
        bk_biz_id: this.$store.getters.bizId,
        index_set_id: data.extendFields.indexSetId || data.extendFields.relatedId
      }).then((data) => {
        data.condition.forEach((item) => {
          this.conditionList.set(item.id, item.name)
        })
        data.dimension.forEach((item) => {
          this.dimensionList.set(item.id, item.name)
        })
      })
        .catch(() => [])
        .finally(() => {
          this.$emit('target-loading', false)
        })
    },
    // 请求conditions变量数据
    getConditonsVar(strategyData) {
      const { aggCondition, dataSourceLabel, dataTypeLabel, metricField, resultTableId } = strategyData
      const promistList = []
      aggCondition.forEach((item) => {
        const params = {
          type: 'dimension',
          params: {
            data_source_label: dataSourceLabel,
            data_type_label: dataTypeLabel,
            field: item.key,
            metric_field: metricField,
            result_table_id: resultTableId,
            where: []
          }
        }
        if (!this.dimensionsValueMap[item.key]) promistList.push(this.getVariableValueList(params))
      })
      return Promise.all(promistList)
    },
    // 处理itemList数据
    async handleChangeItemList(itemList, index) {
      this.handleStrategyName(itemList)
      this.strategyData = itemList[index]
      await this.getConditonsVar(this.strategyData)
      const { strategyData } = this
      if (this.strategyData.dataTypeLabel === 'time_series' && this.$i18n.locale === 'enUS') {
        this.strategyData.name = this.strategyData.metricId
      }
      if (['time_series', 'log'].includes(this.strategyData.dataTypeLabel) && this.$i18n.locale !== 'zhCN') {
        this.strategyData.descVisible = false
      }
      this.handleDetectAlgorithmList(strategyData)
      if (strategyData.dataTypeLabel === 'event' && strategyData.dataSourceLabel === 'bk_monitor') {
        this.eventLevel = strategyData.detectAlgorithmList[0].level
        this.handleEventDimensionList(strategyData)
      } else {
        this.handleDimensionList(strategyData)
      }
    },
    async handleEventDimensionList(data) {
      await this.getDimensionList(data)
      data?.aggCondition.forEach((item) => {
        if (item.condition) {
          this.aggCondition.push(item.condition.toLocaleUpperCase())
        }
        let name = ''
        if (item.key === data.metricField) {
          name = data.name
        } else {
          name = this.conditionList.get(item.key) || item.key
        }
        this.aggCondition.push(name)
        this.aggCondition.push(this.methodMap[item.method])
        this.aggCondition.push(item.valueName || this.handleConditionName(item.value, item.key))
      })
      this.$emit('target-loading', false)
    },
    // 筛出左边监控指标列表
    handleStrategyName(itemList) {
      this.strategyName = itemList.map(item => item.name)
    },
    // 处理检测算法数据
    handleDetectAlgorithmList(data) {
      let expendOnly = false
      this.detectAlgorithmList = this.levelMap.map((item) => {
        const levelItem = data.detectAlgorithmList.find(el => item.level === el.level)
        const algorithmList = levelItem ? levelItem.algorithmList : []
        let expand = false
        if (levelItem && !expendOnly) {
          expand = true
          expendOnly = true
        }
        return {
          name: item.name,
          level: item.level,
          list: algorithmList,
          expand
        }
      })
    },
    // 处理监控项详情数据
    async handleDimensionList(data) {
      const { aggCondition } = this
      const { aggDimension } = this
      if ((data.dataTypeLabel === 'log' && data.dataSourceLabel !== 'bk_monitor')
        || (data.dataSourceLabel === 'bk_log_search' && data.dataTypeLabel === 'time_series')) {
        await this.getLogFields(data)
        data.aggDimension.forEach((item) => {
          const name = this.dimensionList.get(item) || item
          aggDimension.push(name)
        })
        data.aggCondition.forEach((item) => {
          if (item.condition) {
            aggCondition.push(item.condition.toLocaleUpperCase())
          }
          const method = this.conditionList.get(item.method)
          aggCondition.push(item.key)
          aggCondition.push(method)
          aggCondition.push(this.handleConditionName(item.value, item.key))
        })
      } else {
        if (data.dataSourceLabel === 'custom') {
          this.eventLevel = data.detectAlgorithmList[0].level
        }
        await this.getDimensionList(data)
        data.aggDimension.forEach((item) => {
          const name = this.conditionList.get(item) || item
          aggDimension.push(name)
        })
        data.aggCondition.forEach((item) => {
          if (item.condition) {
            aggCondition.push(item.condition.toLocaleUpperCase())
          }
          let name = ''
          if (item.key === data.metricField) {
            name = data.name
          } else {
            name = this.conditionList.get(item.key) || item.key
          }
          aggCondition.push(name)
          aggCondition.push(this.methodMap[item.method])
          aggCondition.push(item.valueName || this.handleConditionName(item.value, item.key))
        })
      }
      this.$emit('target-loading', false)
    },
    handleConditionName(value, key) {
      const list = this.dimensionsValueMap[key]
      if (Array.isArray(value)) {
        return value.map((item) => {
          const res = list.find(set => set.id === `${item}`)
          return res?.name || `${item}`
        })
      }
      const res = list.find(set => set.id === `${value}`)
      return res?.name || `${value}`
    },
    handleLeftEnter(v) {
      this.left.enter = v
    },
    handleLeftLeave() {
      this.left.enter = -1
    },
    handleLeftClick(v) {
      this.left.active = v
    }
  }
}
</script>

<style lang="scss" scoped>
    @import "strategy-detail-mixin";

    .detail-target {
      font-size: 12px;
      color: #63656e;
      .right-form {
        @include common-panel;
        &-title {
          @include common-panel-title;
          .set-desc {
            font-size: 14px;
            color: #c4c6cc;
            &:hover {
              color: #3a84ff;
              cursor: pointer;
            }
          }
        }
        &-item {
          @include common-panel-item;
          .item-agg-dimension {
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: left;
            min-height: 24px;
            line-height: 16px;
            border-radius: 2px;
            background: #f0f1f5;
            margin: 0 2px 2px 0;
            padding: 4px 10px;
          }
          .item-agg-condition {
            background: #fff;
            display: flex;
            flex-wrap: wrap;
            text-align: left;
            margin-right: 40px;
            .item-blue {
              color: #3a84ff;
            }
            .item-yellow {
              color: #ff9c01;
            }
          }
          .item-center {
            flex: 1;
            .item-target-btn {
              cursor: pointer;
              color: #3a84ff;
              display: inline-block;
              margin-left: 10px;
            }
          }
          .item-radio {
            margin-right: 24px;
          }
          /deep/ .bk-radio-text {
            color: #63656e;
          }
        }
      }
    }
</style>
