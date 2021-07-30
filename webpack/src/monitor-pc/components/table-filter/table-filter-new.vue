<template>
  <span :class="['table-filter-wrap', { 'is-active': value.length }]">
    <bk-popover
      ext-cls="menu-list-wrapper"
      ref="selectDropdown"
      trigger="click"
      placement="bottom-start"
      theme="light menu-list-wrapper"
      animation="slide-toggle"
      :transfer="false"
      :arrow="false"
      :tippy-options="tippyOptions"
      :offset="-1"
      :distance="5">
      <span
        ref="target"
        class="table-title-wrap"
        @click="handleShowDropMenu">
        <span class="columns-title">{{title}}</span>
        <i class="icon-monitor icon-filter-fill"></i>
      </span>
      <span slot="content" class="menu-list-wrap" ref="menuList">
        <ul class="menu-list">
          <li class="list-item" v-for="(item, index) in localList" :key="index" @click="item.checked = !item.checked">
            <span @click.stop>
              <bk-checkbox v-model="item.checked" :true-value="true" :false-value="false"></bk-checkbox>
            </span>
            <span class="name">{{ item.name }}</span>
          </li>
        </ul>
        <div class="footer">
          <div class="btn-group">
            <span class="monitor-btn" @click="handleConfirm"> {{ $t('确定') }} </span>
            <span class="monitor-btn" @click="handleCancel"> {{ $t('重置') }} </span>
          </div>
        </div>
      </span>
    </bk-popover>
  </span>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit, Ref, Watch } from 'vue-property-decorator'
import { deepClone } from '../../../monitor-common/utils/utils'

export interface IListItem {
  id: string | number,
  name: string | number,
  checked: boolean
}

@Component({ name: 'table-filter' })
export default class TableFilter extends Vue {
  @Prop({ default: '', type: String }) readonly title: string
  @Prop({ default: () => [], type: Array }) readonly value: any

  @Prop({ default: () => [], type: Array }) readonly list: IListItem[]

  @Prop({ default: () => ({}), type: Object }) readonly tippyOptions: any

  @Ref('target') readonly targetRef: HTMLElement
  @Ref('menuList') readonly menuListRef: HTMLElement

  private localValue: any = []

  private localList: any = []

  @Watch('value', { immediate: true, deep: true })
  @Watch('list', { deep: true })
  handleLocalListChange() {
    this.localList = this.list.map((item) => {
      const temp = deepClone(item)
      temp.checked = this.value.includes(temp.id)
      return temp
    })
  }

  @Emit('change')
  emitValueChange(v?) {
    return v || this.localList.filter(item => item.checked).map(item => item.id)
  }

  private handleShowDropMenu() {
    this.handleLocalListChange()
  }

  private handleConfirm() {
    this.emitValueChange()
    this.close()
  }

  private handleCancel() {
    this.emitValueChange([])
    this.close()
  }

  private getPopoverInstance() {
    return this.$refs.selectDropdown.instance
  }
  private show() {
    const popover = this.getPopoverInstance()
    popover.show()
  }
  private close() {
    const popover = this.getPopoverInstance()
    popover.hide()
  }
}
</script>

<style lang="scss" scoped>
.table-filter-wrap {
  .table-title-wrap {
    cursor: pointer;
  }
}
.is-active {
  .table-title-wrap {
    .icon-filter-fill {
      color: #699df4;
    }
  }
}
</style>

<style lang="scss">
.menu-list-wrapper-theme {
  /* stylelint-disable-next-line declaration-no-important */
  padding: 0 !important;
  width: 100%;
  box-shadow: 0 0 6px rgba(204, 204, 204, .3);
  border-radius: 0;
  .menu-list-wrap {
    display: inline-block;
    min-width: 100px;
    background-color: #fff;
    .menu-list {
      display: flex;
      flex-direction: column;
      border-radius: 2px;
      padding: 6px 0;
      max-height: 250px;
      overflow-y: auto;
      .list-item {
        display: flex;
        align-items: center;
        flex-shrink: 0;
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
      height: 29px;
      border-top: solid 1px #f0f1f5;
      .btn-group {
        display: flex;
        justify-content: space-between;
        align-items: center;
        // width: 70px;
        height: 100%;
        padding: 0 10px;
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
}
</style>
