<template>
  <div class="echart-annotation" v-show="annotation.show" :style="{ left: annotation.x + 'px', top: annotation.y + 'px' }">
    <div class="echart-annotation-title">{{ annotation.title}}</div>
    <div class="echart-annotation-name">
      <span class="name-mark" :style="{ backgroundColor: annotation.color }"></span>{{annotation.name}}
    </div>
    <ul class="echart-annotation-list">
      <template v-for="item in annotation.list">
        <li class="list-item" v-if="item.show" :key="item.id" @click="handleGotoDetail(item)">
          <span class="icon-monitor item-icon" :class="`icon-mc-${item.id}`"></span>
          <span> {{toolBarMap[item.id]}}
            <span v-if="item.id === 'ip'" style="color: #c4c6cc">{{`(${item.value.split('-').reverse().join(':')})`}}</span>
          </span>
          <i class="icon-monitor icon-mc-link list-item-link"></i>
        </li>
      </template>
    </ul>
  </div>
</template>
<script lang="ts">
import { Component, Vue, Prop } from 'vue-property-decorator'
import { IAnnotation, IAnnotationListItem } from '../options/type-interface'
@Component({ name: 'ChartAnnotation' })
export default class ChartAnnotation extends Vue {
  @Prop({ required: true })annotation: IAnnotation
  get toolBarMap() {
    return {
      ip: this.$t('相关主机详情'),
      process: this.$t('相关进程信息'),
      strategy: this.$t('相关策略')
    }
  }
  handleGotoDetail(item: IAnnotationListItem) {
    switch (item.id) {
      case 'ip':
        window.open(location.href.replace(location.hash, `#/performance/detail/${item.value}`))
        break
      case 'process':
        window.open(location.href.replace(
          location.hash,
          `#/performance/detail-new/${item.value.id}/${item.value.processId}`
        ))
        break
      case 'strategy':
        window.open(location.href.replace(location.hash, `#/strategy-config?metricId=${item.value}`))
        break
    }
  }
}
</script>
<style lang="scss" scoped>
.echart-annotation {
  position: absolute;
  min-height: 84px;
  width: 220px;
  background: white;
  border-radius: 2px;
  box-shadow: 0px 4px 12px 0px rgba(0,0,0,.2);
  z-index: 99;
  font-size: 12px;
  color: #63656e;
  &-title {
    margin: 6px 0 0 16px;
    line-height: 20px;
  }
  &-name {
    margin-top: 2px;
    padding-left: 18px;
    height: 20px;
    display: flex;
    align-items: center;
    font-weight: 700;
    border-bottom: 1px solid #f0f1f5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 90%;
    .name-mark {
      flex: 0 0 12px;
      height: 4px;
      margin-right: 10px;
    }
  }
  &-list {
    display: flex;
    flex-direction: column;
    .list-item {
      flex: 0 0 30px;
      display: flex;
      align-items: center;
      padding-left: 16px;
      .item-icon {
        margin-right: 10px;
        font-size: 16px;
        margin-right: 10px;
        height: 16px;
        width: 16px;
      }
      &-link {
        font-size: 12px;
        margin-left: auto;
        margin-right: 6px;
      }
      &:hover {
        background-color: #e1ecff;
        cursor: pointer;
        color: #3a84ff;
      }
    }
  }
}
</style>
