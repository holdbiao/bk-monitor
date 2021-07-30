<template>
  <div class="alarm-shield-detail-scope">
    <div class="scope-item">
      <div class="item-label"> {{ $t('屏蔽范围') }} </div>
      <div class="item-content"><div class="item-content-target">{{target}}</div></div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'alarm-shield-detail-scope',
  props: {
    dimension: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      target: ''
    }
  },
  watch: {
    dimension: {
      handler: 'handleDimension',
      immediate: true,
      deep: true
    }
  },
  methods: {
    // 目前的解决方案是把数组转化成字符串，缺点是展示条数过多会现得密密麻麻，看不清楚 （展示待更改）
    handleDimension(v) {
      if (Object.keys(v).length) {
        this.target = v.target.join(',')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
    .alarm-shield-detail-scope {
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
          &-target {
            word-break: break-all;
            max-width: calc(100vw - 306px);
          }
        }
      }
    }
</style>
