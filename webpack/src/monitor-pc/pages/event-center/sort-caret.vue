<template>
  <span :class="['sort-wrapper', active]">
    <i class="sort-caret ascending"></i>
    <i class="sort-caret descending"></i>
  </span>
</template>
<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator'

@Component({ name: 'sort-caret' })
export default class SortCaret extends Vue {
  @Prop({ required: true }) active: 'normal' | 'asc' | 'desc'
  private list: [
    {
      id: 'asc',
      name: 'asc',
      next: 'desc'
    },
    {
      id: 'desc',
      name: 'desc',
      next: 'normal'
    },
    {
      id: 'normal',
      name: 'normal',
      next: 'asc'
    }
  ]
}
</script>
<style lang="scss" scoped>
.sort-wrapper {
  position: relative;
  height: 20px;
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  &.asc .sort-caret.ascending {
    border-bottom-color: #63656e;
  }
  &.desc .sort-caret.descending {
    border-top-color: #63656e;
  }
  .sort-caret {
    width: 0;
    height: 0;
    border: 5px solid transparent;
    position: absolute;
    &.ascending {
      border-bottom-color: #c0c4cc;
      top: -1px;
    }
    &.descending {
      border-top-color: #c0c4cc;
      bottom: -1px;
    }
  }
}
</style>
