<template>
  <div class="alarm-shield-detail-strategy">
    <div class="scope-item  adapt-icon">
      <div class="item-label"> {{ $t('屏蔽策略') }} </div>
      <div class="item-content">
        <div v-for="(item, index) in dimension.strategies" :key="item.id" class="item-content-name">
          {{ item.name }}<i class="icon-monitor icon-mc-wailian" @click="handleToStrategy(item.id)"></i>
          <span v-if="index + 1 !== dimension.strategies.length">,</span>
        </div>
      </div>
    </div>
    <div class="strategy-detail" v-if="isOneStrategy">
      <div class="strategy-detail-label"> {{ $t('策略内容') }} </div>
      <strategy-detail :strategy-data="dimension.strategies[0].itemList[0]"></strategy-detail>
    </div>
    <div class="scope-item" v-if="dimension.target">
      <div class="item-label"> {{ $t('屏蔽范围') }} </div>
      <div class="item-content">
        <div class="item-content-target">{{ target }}</div>
      </div>
    </div>
    <div class="scope-item">
      <div class="item-label"> {{ $t('屏蔽级别') }} </div>
      <div class="item-content">{{ level }}</div>
    </div>
  </div>
</template>

<script>
import { strategyMapMixin } from '../../../common/mixins'
import StrategyDetail from '../alarm-shield-components/strategy-detail'
export default {
  name: 'alarm-shield-detail-strategy',
  components: {
    StrategyDetail
  },
  mixins: [strategyMapMixin],
  props: {
    dimension: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      level: '',
      levelMap: ['', this.$t('致命'), this.$t('预警'), this.$t('提醒')],
      target: ''
    }
  },
  computed: {
    isOneStrategy() {
      return this.dimension.strategies.length === 1
    }
  },
  created() {
    this.handleStrategyDetail()
  },
  methods: {
    handleStrategyDetail() {
      const arr = []
      this.dimension.level.forEach((item) => {
        arr.push(this.levelMap[item])
      })
      this.level = arr.join('、')
      if (this.dimension.target) {
        this.target = this.dimension.target.join(',')
      }
    },
    handleToStrategy(id) {
      this.$router.push({ name: 'strategy-config-detail', params: { id } })
    }
  }
}
</script>

<style lang="scss" scoped>
  .alarm-shield-detail-strategy {
    font-size: 14px;
    color: #63656e;
    .scope-item {
      display: flex;
      align-items: flex-start;
      margin-bottom: 20px;
      .item-label {
        min-width: 90px;
        color: #979ba5;
        text-align: right;
        margin-right: 24px;
      }
      .item-content {
        min-height: 16px;
        display: flex;
        align-items: center;
        &-name {
          display: flex;
          align-items: center;
        }
        i {
          font-size: 21px;
          color: #979ba5;
          cursor: pointer;
          &:hover {
            color: #3a84ff;
          }
        }
        &-target {
          word-break: break-all;
          max-width: calc(100vw - 306px);
        }
      }
    }
    .adapt-icon {
      /* stylelint-disable-next-line declaration-no-important */
      align-items: center !important;
      .item-content {
        line-height: 23px;
      }
    }
    .strategy-detail {
      display: flex;
      align-items: flex-start;
      margin-bottom: 20px;
      &-label {
        color: #979ba5;
        min-width: 90px;
        text-align: right;
        margin-right: 24px;
        padding-top: 6px;
      }
      &-content {
        display: flex;
        flex-direction: column;
        padding: 11.5px 21px 6px 21px;
        width: calc(100vw - 306px);
        background: #fafbfd;
        border: 1px solid #dcdee5;
        border-radius: 2px;
        .column-item {
          min-height: 32px;
          display: flex;
          align-items: flex-start;
          margin-bottom: 7px;
        }
        .item-label {
          min-width: 70px;
          text-align: right;
          height: 32px;
          line-height: 32px;
          margin-right: 6px;
        }
        .item-content {
          height: 32px;
          line-height: 32px;
        }
        .item-aggdimension {
          background: #fff;
          font-size: 12px;
          text-align: center;
          height: 32px;
          line-height: 16px;
          border-radius: 2px;
          border: 1px solid #dcdee5;
          margin: 0 2px 2px 0;
          padding: 7px 12px 9px 12px;
        }
        .item-aggcondition {
          max-width: calc(100vw - 322px);
          display: flex;
          flex-wrap: wrap;
          .item-blue {
            color: #3a84ff;
          }
          .item-yellow {
            color: #ff9c01;
          }
        }
        &-aggCondition {
          align-items: flex-start;
        }
      }
    }
  }
</style>
