<template>
  <div :class="['member-selector-wrap', { 'is-error': isError }]">
    <bk-user-selector
      class="bk-user-selector"
      v-model="localValue"
      :panel-width="300"
      :placeholder="$t('请选择通知对象')"
      :display-tag-tips="true"
      :display-domain="false"
      :tag-tips-content="handleTabTips"
      :tag-clearable="false"
      :fast-clear="true"
      :default-alternate="() => deepClone(groupList)"
      :empty-text="$t('无匹配人员')"
      :render-list="renderUserSelectorList"
      :render-tag="renderUserSelectorTag"
      :api="bkUrl"
      @focus="handleFocus"
      @change="emitLocalValue">
    </bk-user-selector>
  </div>
</template>

<script lang="ts">
import { Component, Mixins, Prop, Model, Emit, Watch } from 'vue-property-decorator'
import { memberSelectorMixin } from '../../../common/mixins'
import { deepClone } from '../../../../monitor-common/utils/utils'
import BkUserSelector from '@blueking/user-selector'

@Component({
  name: 'member-selector',
  components: {
    BkUserSelector
  }
})
export default class MemberSelector extends Mixins(memberSelectorMixin) {
  @Prop({ type: Array, default: () => [] }) readonly groupList: any
  @Model('localValueChange', { type: Array, default: () => [] }) value: string[]

  localValue: string[] = []

  deepClone: Function = null

  // 人员选择器api地址
  get bkUrl() {
    const { bkUrl } = this.$store.getters
    const origin = /^https?:\/\/[\w-.]+/i.exec(bkUrl)[0]
    return `${origin}/api/c/compapi/v2/usermanage/fs_list_users/`
  }

  get isError() {
    return this.$parent?.validator?.state === 'error'
  }

  @Watch('value')
  handleValueChange() {
    this.localValue = this.value
  }

  @Emit('localValueChange')
  emitLocalValue() {
    return deepClone(this.localValue)
  }

  created() {
    this.deepClone = deepClone
  }

  // 人员选择器tag render
  renderUserSelectorTag(h, tag) {
    const groupName = this.getDefaultUsername(this.groupList, tag.username)
    const renderTag = {
      display_name: groupName || tag.user?.['display_name'] || tag.username,
      id: tag.username,
      type: groupName ? 'group' : ''
    }
    return this.renderMemberTag(renderTag)
  }
  // 人员选择器list render
  renderUserSelectorList(h, item) {
    const { user } = item
    const renderListItem = {
      type: user.type,
      index: user.index,
      id: user.username,
      display_name: user.display_name
    }
    return this.renderMerberList(renderListItem)
  }
  // tag提示
  handleTabTips(val) {
    return this.getDefaultUsername(this.groupList, val) || val
  }
  // 查找display_name
  getDefaultUsername(list, val) {
    for (const item of list) {
      if (item.username === val) return item.display_name
      if (item.children && item.children.length) return this.getDefaultUsername(item.children, val)
    }
  }

  handleFocus() {
    this.$parent?.handlerFocus && this.$parent.handlerFocus()
  }
}
</script>

<style lang="scss" scoped>
.member-selector-wrap {
  .bk-user-selector {
    width: 100%;
    /deep/ .user-selector-selected {
      background: none;
    }
  }
}
.is-error {
  /deep/.user-selector-container {
    border-color: #ff5656;
  }
}
.tag,
.bk-selector-member {
  display: flex;
}
.only-notice {
  display: flex;
  align-items: center;
  padding-left: 10px;
}
.only-img {
  color: #979ba5;
  font-size: 22px;
  background: #fafbfd;
  border-radius: 16px;
  margin-right: 5px;
}
/deep/.bk-form-control {
  background: #fff;
}
</style>
