<template>
  <div class="label-menu-wrapper">
    <ul class="label-menu-list">
      <li class="item"
          v-for="(item, index) in list"
          :key="index"
          @click="handleCheck(item)">
        <bk-checkbox :value="item.checked"></bk-checkbox>
        <span class="name">{{ item.name }}</span>
      </li>
    </ul>
    <div class="footer">
      <div class="btn-group">
        <span
          class="monitor-btn"
          @click="handleConfirm">
          {{ $t('确定') }}
        </span>
        <span
          class="monitor-btn"
          @click="handleClear">
          {{ $t('清空') }}
        </span>
      </div>
    </div>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Emit } from 'vue-property-decorator'

interface IOption {
  id: string
  name: string
  checked: boolean
}

@Component({ name: 'label-menu' })
export default class LabelMenu extends Vue {
  public list: IOption[] = []

  @Emit('confirm')
  public handleConfirm() {
    return this.list
  }

  @Emit('clear')
  public handleClear() {
    this.list.forEach((item) => {
      item.checked = false
    })
    return this.list
  }

  public handleCheck(item: IOption) {
    item.checked = !item.checked
  }
}
</script>
<style lang="scss" scoped>
.label-menu-wrapper {
  .label-menu-list {
    display: flex;
    flex-direction: column;
    background-color: #fff;
    border-radius: 2px;
    padding: 6px 0;
    .item {
      display: flex;
      align-items: center;
      height: 32px;
      padding: 0 10px;
      color: #63656e;
      cursor: pointer;
      .name {
        margin-left: 6px;
      }
      &:hover {
        background: #e1ecff;
        color: #3a84ff;
      }
    }
  }
  .footer {
    padding: 0 10px;
    display: flex;
    justify-content: center;
    height: 32px;
    border-top: solid 2px #f0f1f5;
    background-color: #fff;
    .btn-group {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 70px;
      height: 100%;
      .monitor-btn {
        color: #3a84ff;
        cursor: pointer;
        &:hover {
          color: #699df4;
        }
      }
    }
  }
}
</style>
