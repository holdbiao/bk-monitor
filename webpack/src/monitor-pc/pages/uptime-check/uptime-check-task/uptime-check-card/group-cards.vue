<template>
  <div class="group-task" v-show="!taskDetail.show && hasGroupList">
    <div class="group-task-header">
      <span class="header-name"> {{ $t('拨测任务组') }} </span>
    </div>
    <div class="group-task-wrap" ref="cardWrap" :style="{ height: wrapHeight + 'px' }">
      <div class="group-task-wrap-list" ref="cardWrapList">
        <div class="group-task-wrap-list-item"
             v-for="(item,index) in group"
             v-show="item.name.includes(keyword)"
             :key="index"
             :ref="'task-item-' + index"
             :class="{ 'drag-active': index === drag.active }"
             @click.stop="handleItemClick(item)"
             @dragover="handleDragOver(index, item, $event)"
             @dragleave="handleDragLeave(index, item, $event)"
             @dragenter="handleDragEnter(index, item, $event)"
             @drop="handleDragDrop(index, item, $event)"
             @mouseenter="handleGroupMouseEnter(index)"
             @mouseleave="handleGroupMouseLeave(item, index)">
          <div class="item-desc">
            <span class="desc-icon"
                  :style="{ 'background-image': item.logo ? `url(${item.logo})` : 'none','background-color': item.logo ? '' : '#B6CAEC', 'border-radius': item.logo ? '0' : '100%' }">
              {{!item.logo ? item.name.slice(0,1).toLocaleUpperCase() : ''}}
            </span>
            <div class="desc-right">
              <div class="desc-right-title">{{item.name}}<span class="alarm-label" v-if="item.alarm_num">{{item.alarm_num}}</span></div>
              <div class="desc-right-label">
                <span class="right-label" v-for="(set,name) in item.protocol_num" :key="name">{{`${set.name}(${set.val})`}}</span>
                <span v-if="!item.protocol_num || !item.protocol_num.length" class="right-label"> {{ $t('空任务组') }} </span>
              </div>
              <span class="desc-right-icon"
                    v-authority="{ active: !authority.MANAGE_AUTH }"
                    v-if="hoverActive === index"
                    :ref="'popover-' + index"
                    :class="{ 'hover-active': popover.hover }"
                    @click.stop="authority.MANAGE_AUTH ? handlePopoverShow(item, index, $event) : handleShowAuthorityDetail()"
                    @mouseleave="handleGroupPopoverLeave"
                    @mouseover="popover.hover = true">
                <i class="bk-icon icon-more"></i>
              </span>
            </div>
          </div>
          <div class="item-list" v-if="item.top_three_tasks.length">
            <div v-for="(pro,i) in item.top_three_tasks" :key="i" class="item-list-progress">
              <div class="progress-desc">
                <span class="desc-name">{{pro.name}}</span>
                <span class="desc-percent">{{pro.available !== null ? pro.available + '%' : '--'}}</span>
              </div>
              <bk-progress class="progress-item" :percent="+(pro.available * 0.01).toFixed(2) || 0" :show-text="false" :color="pro.available | filterProcess"></bk-progress>
            </div>
          </div>
          <div v-else class="item-empty">
            <div class="item-empty-item"> {{ $t('暂无拨测任务') }} </div>
            <div class="item-empty-item"> {{ $t('可以拖动拨测任务至此') }} </div>
          </div>
        </div>
      </div>
    </div>
    <div class="more-btn-wrap" v-if="needExpand && !expand" @click="handleExpand">
      <span class="more-btn">{{$t('显示全部')}}<i class="icon-monitor icon-double-down"></i></span>
    </div>
    <div v-show="false">
      <div class="popover-desc" ref="popoverContent">
        <div class="popover-desc-btn" @click.stop="handleEditGroup"> {{ $t('编辑') }} </div>
        <div class="popover-desc-btn" @click.stop="handleDeleteGroup"> {{ $t('解散任务组') }} </div>
      </div>
    </div>
    <bk-dialog class="bk-dialog-edit" v-model="dialog.edit.show" :title="dialog.edit.add ? $t('新建拨测任务组') : $t('编辑拨测任务组')" header-position="left" width="480" @after-leave="fixStyle">
      <div class="dialog-edit">
        <div class="dialog-edit-content">
          <div>
            <div class="dialog-edit-label"> {{ $t('任务组名称') }} </div>
            <bk-input
              @blur="dialog.edit.validate = !dialog.edit.name.length"
              :class="{ 'dialog-edit-input': dialog.edit.validate }" :placeholder="$t('请输入拨测任务组名称')"
              v-model="dialog.edit.name"
              @change="dialog.edit.validate = !dialog.edit.name.length">
            </bk-input>
            <div v-show="dialog.edit.validate" class="dialog-edit-validate">{{ dialog.edit.message || '请输入拨测任务组名称'}}</div>
          </div>
          <div v-if="false">
            <div class="dialog-edit-label"> {{ $t('所属业务') }} </div>
            <bk-select :placeholder="$t('请选择所属业务')" :disabled="bizId !== 0" v-model="dialog.edit.bizId">
              <bk-option
                class="dialog-edit-option"
                v-for="item in bizList"
                :id="item.id"
                :name="item.text"
                :key="item.id">
              </bk-option>
            </bk-select>
          </div>
          <div>
            <div class="dialog-edit-label"> {{ $t('选择拨测任务') }} </div>
            <bk-select
              class="dialog-edit-select"
              v-model="dialog.edit.select"
              multiple :placeholder="$t('请选择拨测任务')">
              <bk-option
                class="dialog-edit-option"
                v-for="item in taskList"
                :id="item.id"
                :name="item.name"
                :key="item.id">
              </bk-option>
            </bk-select>
          </div>
        </div>
        <div class="dialog-edit-upload">
          <div class="dialog-edit-logo"
               @mouseover="dialog.edit.close = true"
               @mouseleave="dialog.edit.close = false"
               :style="{ 'background-image': dialog.edit.logo ? `url(${dialog.edit.logo})` : 'none' }">
            {{ !dialog.edit.logo ? 'LOGO' : '' }}
            <div v-show="dialog.edit.close" class="logo-mask">{{ !!dialog.edit.logo ? $t('点击更换') : $t('点击上传')}}</div>
            <i v-show="dialog.edit.close && !!dialog.edit.logo" class="bk-icon icon-close" @click.stop.prevent="handleDeleteLogo"></i>
            <input type="file" class="edit-logo" title="" accept="image/png" @change="handleUploadChange" />
          </div>
        </div>
      </div>
      <div slot="footer">
        <bk-button theme="primary" :disabled="dialog.edit.validate" @click="handleSubmitEdit"> {{ $t('确定') }} </bk-button>
        <bk-button @click="handleCancel"> {{ $t('取消') }} </bk-button>
      </div>
    </bk-dialog>
  </div>
</template>
<script>
import { uptimeCheckMixin } from '../../../../common/mixins'
import { createNamespacedHelpers } from 'vuex'
const { mapGetters } = createNamespacedHelpers('uptime-check-task')
export default {
  name: 'GroupCards',
  mixins: [uptimeCheckMixin],
  props: {
    group: {
      type: Array,
      default() {
        return []
      }
    },
    taskDetail: {
      type: Object,
      required: true
    },
    itemWidth: Number
  },
  inject: ['authority', 'handleShowAuthorityDetail'],
  data() {
    const defaultEdit = this.getDefaultEditDialog()
    return {
      expand: false,
      needExpand: false,
      wrapHeight: 240,
      hoverActive: -1,
      popoverOptions: {
        appendTo: this.handleAppendTo
      },
      dialog: {
        edit: defaultEdit,
        delete: {
          id: ''
        }
      },
      drag: {
        active: -1
      },
      popover: {
        hover: false,
        instance: null,
        active: -1
      }

    }
  },
  computed: {
    ...mapGetters(['keyword', 'taskList']),
    bizList() {
      return this.$store.getters.bizList
    },
    bizId() {
      return this.$store.getters.bizId
    },
    hasGroupList() {
      return !!(this.group.filter(item => item.name.includes(this.keyword)) || []).length
    }
  },
  watch: {
    expand(v) {
      this.wrapHeight = v && this.needExpand ? this.$refs.cardWrapList.getBoundingClientRect().height : 240
    },
    itemWidth: {
      handler: 'handleWindowResize'
    },
    group: {
      handler: 'handleGroupChange',
      deep: true
    }
  },
  mounted() {
    this.handleGroupChange()
    this.$bus.$on('handle-create-task-group', this.handleAddGroup)
  },
  destroyed() {
    this.$bus.$off('handle-create-task-group')
  },
  methods: {
    handleDeleteLogo() {
      const { edit } = this.dialog
      edit.logo = ''
      edit.close = false
    },
    handleUploadChange(eve) {
      const e = eve
      const file = e.target.files[0]
      const fileReader = new FileReader()
      fileReader.onloadend = (event) => {
        this.dialog.edit.logo = event.target.result
        e.target.value = ''
      }
      fileReader.readAsDataURL(file)
    },
    handleGroupChange() {
      setTimeout(() => {
        this.needExpand = this.$refs.cardWrapList.getBoundingClientRect().height > 240
        this.expand = this.expand && this.needExpand
        this.$nextTick().then(() => {
          this.handleWindowResize()
        })
      }, 16)
    },
    refreshItemWidth() {
      this.handleWindowResize()
    },
    handleWindowResize() {
      const len = this.group.length
      const width = (this.$refs['task-item-0'] && this.$refs['task-item-0'].length)
        ? this.$refs['task-item-0'][0].getBoundingClientRect().width : 400
      if (len > 0) {
        let i = 0
        while (i < len) {
          const ref = this.$refs[`task-item-${i}`][0]
          if (ref && ref.getBoundingClientRect().width !== width) {
            ref.style.maxWidth = `${width || 400}px`
          }
          i += 1
        }
      }
      const { height } = this.$refs.cardWrapList.getBoundingClientRect()
      if (this.expand) {
        this.wrapHeight = height || this.wrapHeight
      }
      this.needExpand = (height || this.wrapHeight) > 240
    },
    getDefaultEditDialog() {
      return {
        add: true,
        id: '',
        show: false,
        name: '',
        bizId: +this.$store.getters.bizId,
        select: [],
        validate: false,
        logo: '',
        close: false,
        message: '',
        active: -1
      }
    },
    handleItemClick(item) {
      if (item.all_tasks && item.all_tasks.length) {
        this.$emit(
          'update:taskDetail',
          { show: true, tasks: item.all_tasks.map(task => task.task_id), name: item.name, id: item.id }
        )
      }
    },
    handleGroupMouseEnter(index) {
      this.hoverActive = index
      this.dialog.edit.active = index
    },
    handleGroupMouseLeave() {
      this.hoverActive = -1
      this.popover.hover = false
    },
    handlePopoverShow(item, index, e) {
      this.popover.instance = this.$bkPopover(e.target, {
        content: this.$refs.popoverContent,
        arrow: false,
        trigger: 'click',
        placement: 'bottom',
        theme: 'light group-card',
        maxWidth: 520,
        duration: [275, 0],
        offset: '-6',
        appendTo: () => this.$refs[`popover-${index}`][0],
        onHidden: () => {
          this.popover.hover = false
        }
      })
      // .instances[0]
      this.popover.active = index
      this.popover.instance && this.popover.instance.show(100)
    },
    handleGroupPopoverLeave() {
      this.popover.hover = this.popover.active >= 0
      !this.popover.hover && this.handlePopoverHide()
    },
    handlePopoverHide() {
      this.popover.instance && this.popover.instance.hide(100)
      this.popover.instance && this.popover.instance.destroy()
      this.popover.instance = null
    },
    handleExpand() {
      this.expand = !this.expand
    },
    handleAppendTo() {
      return this.$refs[`popover-${this.hoverActive}`][0]
    },
    handleEditGroup() {
      const item = this.group[this.hoverActive > -1 ? this.hoverActive : this.dialog.edit.active]
      this.dialog.edit.name = item.name
      this.dialog.edit.id = item.id
      this.dialog.edit.bizId = item.bk_biz_id
      this.dialog.edit.add = false
      this.dialog.edit.show = true
      this.dialog.edit.logo = item.logo
      this.dialog.edit.close = false
      this.dialog.edit.validate = false
      this.dialog.edit.select = item.all_tasks.map(task => task.task_id)
      this.dialog.edit.oriName = item.name
    },
    handleAddGroup() {
      this.dialog.edit = this.getDefaultEditDialog()
      this.dialog.edit.show = true
    },
    handleDeleteGroup() {
      const item = this.group[this.hoverActive > -1 ? this.hoverActive : this.dialog.edit.active]
      this.dialog.delete.id = item.id
      this.$bkInfo({
        title: this.$t('确定解散任务组'),
        subTitle: this.$t('该操作仅删除任务组，不会影响组内拨测任务'),
        confirmFn: () => this.handleSubmitDelete()
      })
    },
    handleSubmitDelete() {
      this.$emit('group-delete', this.dialog.delete.id)
    },
    async handleSubmitEdit() {
      const { edit } = this.dialog
      edit.name = (`${edit.name}`).trim()
      const item = this.group[this.hoverActive > -1 ? this.hoverActive : this.dialog.edit.active]
      if (!edit.name.length) {
        edit.validate = true
        return
      } if (/["/[\]':;|=,+*?<>{}.\\]+/g.test(edit.name)) {
        edit.validate = true
        edit.message = `${this.$t('不允许包含如下特殊字符：')} " / \\ [ ]' : ; | = , + * ? < > { } ${this.$t('空格')}`
        return
      } if (this.validateStrLength(edit.name, 20)) {
        edit.validate = true
        edit.message = this.$t('最多不可超过20个字符（相当于10个中文汉字）')
        return
      } if (
        (edit.add && this.group.find(item => item.name.toLowerCase() === edit.name.toLowerCase()))
        || (!edit.add
            && (edit.name.toLowerCase() !== edit.oriName.toLowerCase()
                && this.group.find(set => set.name.toLowerCase() === edit.name.toLowerCase()))
        )
      ) {
        edit.validate = true
        edit.message = this.$t('该任务组名称已存在，请修改')
        return
      }
      let { logo } = this.dialog.edit
      if (logo) {
        logo = await this.handleImg2Base64(logo)
      }
      if (edit.add
      || !(edit.name === item.name && edit.logo === item.logo
        && edit.select.sort().join(',') === item.all_tasks.map(i => i.task_id).sort()
          .join(','))) {
        this.$emit('group-edit', {
          add: this.dialog.edit.add,
          id: this.dialog.edit.id,
          name: this.dialog.edit.name,
          logo,
          task_id_list: this.dialog.edit.select,
          bk_biz_id: this.bizId
        })
      }
      this.dialog.edit.show = false
    },
    handleCancel() {
      this.dialog.edit.show = false
      this.dialog.edit.active = -1
    },
    handleImg2Base64(logo) {
      return new Promise((resolve) => {
        try {
          const img = new Image()
          const canvas = document.createElement('canvas')
          const context = canvas.getContext('2d')
          img.src = logo
          img.onload = () => {
            const width = Math.min(88, img.width)
            const height = Math.min(88, img.height)
            canvas.width = width
            canvas.height = height
            context.clearRect(0, 0, width, height)
            context.drawImage(img, 0, 0, width, height)
            resolve(canvas.toDataURL())
          }
        } catch {
          resolve('')
        }
      })
    },
    handleDragOver(index, item, e) {
      const event = e
      this.drag.active = index
      event.dataTransfer.dropEffect = 'move'
      event.preventDefault()
    },
    handleDragLeave() {
      this.drag.active = -1
    },
    handleDragEnter(index) {
      this.drag.active = index
    },
    handleDragDrop(index, item, e) {
      e.preventDefault()
      const data = e.dataTransfer.getData('text')
      this.$emit('drag-drop', data, item)
      this.drag.active = -1
    },
    /**
             * @desc 临时处理bk-dialog关闭后覆盖overflow的样式问题
             */
    fixStyle() {
      const t = setTimeout(() => {
        document.querySelector('body').style.overflowY = 'auto'
        clearTimeout(t)
      }, 300)
    },
    validateStrLength(str, length = 50) {
      const cnLength = (str.match(/[\u4e00-\u9fa5]/g) || []).length
      const enLength = (str || '').length - cnLength
      const res = cnLength * 2
      return res + enLength > length
    }
  }
}
</script>
<style lang="scss" scoped>
.group-task {
  margin-bottom: 30px;
  &-header {
    display: flex;
    align-items: center;
    font-size: 14px;
    margin-bottom: 14px;
    .header-name {
      color: #313238;
      font-weight: bold;
      flex: 1;
    }
    .header-expand {
      color: #3a84ff;
      cursor: pointer;
    }
  }
  &-wrap {
    transition: all .4s cubic-bezier(.23, 1, .23, 1);
    overflow: hidden;
    &-list {
      display: flex;
      margin-right: -20px;
      flex-wrap: wrap;
      &-item {
        flex: 1;
        min-width: 300px;
        max-width: 400px;
        height: 220px;
        background: #fff;
        border-radius: 2px;
        border: 1px solid #dcdee5;
        padding: 24px;
        margin-right: 20px;
        margin-bottom: 20px;
        position: relative;
        &:hover {
          box-shadow: 0px 3px 6px 0px rgba(58,132,255,.1);
          cursor: pointer;
        }
        &.drag-active {
          border: 1px dashed #3a84ff;
        }
        .item-desc {
          display: flex;
          align-items: center;
          margin-bottom: 22px;
          .desc-icon {
            flex: 0 0 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 16px;
            font-weight: bold;
            margin-right: 10px;
            background-size: cover;
          }
          .desc-right {
            display: flex;
            flex-direction: column;
            justify-content: center;
            &-title {
              color: #313238;
              font-size: 14px;
              font-weight: bold;
              margin-bottom: 8px;
              display: flex;
              align-items: center;
              .alarm-label {
                display: inline-block;
                margin-left: 10px;
                padding: 0 9px;
                color: #fff;
                border-radius: 15px;
                background: #ea3636;
                font-size: 12px;
              }
            }
            &-label {
              display: flex;
              align-items: center;
              font-size: 12px;
              color: #979ba5;
              .right-label {
                background: #f0f1f5;
                border-radius: 2px;
                padding: 1px 6px;
                margin-right: 6px;
              }
            }
            &-icon {
              position: absolute;
              right: 14px;
              top: 14px;
              color: #63656e;
              font-size: 18px;
              width: 32px;
              height: 32px;
              display: flex;
              justify-content: center;
              align-items: center;
              cursor: pointer;
              transition: background-clor .2s ease-in-out;
              &.hover-active {
                background-color: #f0f1f5;
                border-radius: 50%;
                color: #3a84ff;
              }
            }
          }
        }
        .item-list {
          color: #63656e;
          font-size: 12px;
          &-progress {
            display: flex;
            flex-direction: column;
            margin-bottom: 16px;
            .progress-desc {
              display: flex;
              margin-bottom: 6px;
              .desc-name {
                flex: 1
              }
              .desc-percent {
                color: #979ba5;
              }
            }
            .progress-item {
              /deep/ .progress-bar {
                box-shadow: none;
              }
            }
          }
        }
        .item-empty {
          text-align: center;
          color: #979ba5;
          font-size: 12px;
          overflow: hidden;
          :first-child {
            margin-top: 16px;
          }
        }
      }
      .item-add-new {
        display: flex;
        align-items: center;
        justify-content: center;
        color: #63656e;
        border: 1px dashed #c4c6cc;
        background: #fafbfd;
        cursor: pointer;
        div {
          font-size: 14px;
          cursor: pointer;
          display: flex;
          align-items: center;
        }
        i {
          font-size: 14px;
          font-weight: bold;
          margin-right: 9px;
          color: #c4c6cc;
        }
      }
    }
    .empty-search-data {
      height: 60px;
      background: rgb(251, 252, 253);
      border: 1px solid #dcdee5;
      text-align: center;
      line-height: 60px;
      font-size: 18px;
      color: #979ba5;
    }
  }
  .popover-desc {
    display: flex;
    flex-direction: column;
    color: #63656e;
    font-size: 12px;
    border-radius: 2px;
    border: 1px solid #dcdee5;
    min-width: 75px;
    padding: 6px 0;
    &-btn {
      display: flex;
      align-items: center;
      justify-content: flex-start;
      padding-left: 10px;
      height: 32px;
      background: #fff;
      // &:first-child {
      //     border-bottom: 1px solid #DCDEE5;
      // }
      &:hover {
        background: #f0f1f5;
        color: #3a84ff;
        cursor: pointer;
      }
    }
  }
  .more-btn-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    color: #0083ff;
    font-size: 12;
    margin-top: -8px;
    transition: all .2s ease-in-out;
    cursor: pointer;
    .icon-double-down {
      font-size: 16px;
      vertical-align: middle;
    }
    &:hover {
      background-color: #fff;
    }
  }
}
.bk-dialog-edit {
  /deep/ .bk-dialog-footer {
    padding: 9px 24px;
  }
}
.dialog-edit {
  display: flex;
  height: 134px;
  margin-top: -7px;
  &-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-right: 24px;
  }
  &-label {
    margin-bottom: 8px;
  }
  &-select {
    width: 320px;
  }
  &-input {
    /deep/ input {
      border: 1px solid #ea3636;
    }
  }
  &-validate {
    font-size: 12px;
    color: #ea3636;
  }
  &-upload {
    width: 86px;
    text-align: center;
  }
  &-logo {
    background: #fafbfd;
    border: 1px dashed #dcdee5;
    border-radius: 2px;
    font-size: 12px;
    color: #979ba5;
    text-align: center;
    line-height: 86px;
    height: 86px;
    width: 86px;
    margin-top: 29px;
    margin-bottom: 10px;
    position: relative;
    background-size: cover;
    &:hover {
      border-color: #3a84ff;
    }
    .edit-logo {
      position: absolute;
      width: 84px;
      top: 0;
      left: 0;
      bottom: 0;
      right: 0;
      opacity: 0;
      cursor: pointer;
      z-index: 1;
    }
    .icon-close {
      position: absolute;
      right: 2px;
      top: 2px;
      z-index: 2;
      cursor: pointer;
      color: #fff;
    }
    .logo-mask {
      height: 84px;
      width: 84px;
      position: absolute;
      top: 0;
      left: 0;
      background: #000;
      opacity: .5;
      color: #fff;
      font-size: 14px;
      z-index: 0;
    }
  }
  &-option {
    width: 320px;
  }
}
.dialog-delete {
  color: #63656e;
  font-size: 14px;
  line-height: 19px;
}
</style>
