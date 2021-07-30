<template>
  <div class="export-table-form">
    <!-- 标题 -->
    <div class="table-title">{{ name }}</div>
    <!-- 表格 -->
    <div v-if="list.length" class="table-content">
      <!-- 全选 -->
      <bk-checkbox :value="allElection" :indeterminate="indeterminate" @change="handleAllElection">
        <div class="content-checkbox">
          <div>{{ $t('全选') }}&nbsp;&nbsp;<span class="gray"> {{ $t('共计') }} </span>&nbsp;{{ list.length }}&nbsp;<span class="gray">{{ $t('项') }}</span></div>
          <div>{{ $t('已选') }}&nbsp;<span class="blue">{{ groupChecked.length }}</span>&nbsp;{{ $t('项') }}</div>
        </div>
      </bk-checkbox>
      <!-- 单选 -->
      <bk-checkbox-group v-model="groupChecked" @change="handleCheckChange">
        <div v-for="(item, index) in list" :key="index"
             @mouseenter="handleTableRowEnter(index)"
             @mouseleave="handleTableRowLeave">
          <bk-checkbox :value="item.id">
            <div class="content-checkbox">
              <div class="font">{{ item.name }}<span>（#{{ item.id }}）</span></div>
              <div class="icon" v-show="hover === index">
                <i v-if="item.dependencyPlugin"
                   class="icon-monitor icon-mc-guanlian"
                   @mouseenter.self="handleIconEnter($event, item.dependencyPlugin)"
                   @mouseleave.self="handleIconLeave"
                   ref="Icon"></i>
                <i class="icon-monitor icon-mc-wailian"
                   @click.stop="handleToDetail(item.id)">
                </i>
              </div>
            </div>
          </bk-checkbox>
        </div>
      </bk-checkbox-group>
    </div>
    <!-- 无数据 -->
    <div v-else class="content-none">
      <i class="icon-monitor icon-hint"></i>
      <div> {{ $t('暂无可导出的') }} {{ name }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'export-configuration-forms',
  props: {
    // form 数据
    list: {
      type: Array,
      default: () => ([])
    },
    // 标题
    name: {
      type: String,
      default: ''
    },
    // 跳转路由
    routeName: {
      type: String,
      default: ''
    },
    // 已勾选ID
    checked: {
      type: Array,
      default: () => ([])
    }
  },
  inject: ['authority', 'handleShowAuthorityDetail'],
  data() {
    return {
      groupChecked: [],
      hover: -1,
      popover: {
        index: -1,
        instance: null
      }
    }
  },
  computed: {
    // 全选的状态
    allElection() {
      return this.groupChecked.length === this.list.length
    },
    // 半选的状态
    indeterminate() {
      return this.groupChecked.length !== 0
    }
  },
  watch: {
    // 数据切换时，清空勾选
    list() {
      this.groupChecked = []
      this.$emit('check-change', [])
    },
    checked(newV) {
      this.groupChecked = newV
    }
  },
  methods: {
    // 勾选触发的回调函数
    handleCheckChange(newV) {
      this.$emit('check-change', newV)
    },
    // 表格行鼠标划入高亮事件
    handleTableRowEnter(index) {
      this.hover = index
    },
    // 表格行鼠标划出事件
    handleTableRowLeave() {
      this.hover = -1
    },
    // 行内icon hover划入事件
    handleIconEnter(event, text) {
      if (text) {
        this.popover.instance = this.$bkPopover(event.target, {
          content: text,
          arrow: true,
          hideOnClick: false
        })
        this.popover.instance.show(100)
      }
    },
    // 行内icon hover划出事件
    handleIconLeave() {
      if (this.popover.instance) {
        this.popover.instance.hide(0)
        this.popover.instance.destroy()
        this.popover.instance = null
      }
    },
    // 全选事件
    handleAllElection() {
      if (this.allElection) {
        this.groupChecked = []
      } else {
        this.groupChecked = this.list.map(item => item.id)
      }
      this.$emit('check-change', this.groupChecked)
    },
    // 跳转详情事件
    handleToDetail(id) {
      if (this.routeName === 'strategy-config-detail') {
        const { href } = this.$router.resolve({
          name: 'strategy-config-detail',
          params: { id }
        })
        window.open(href, '_blank')
      } else {
        const { href } = this.$router.resolve({
          name: this.routeName,
          query: { id }
        })
        window.open(href, '_blank')
      }
    }
  }
}
</script>

<style lang="scss" scoped>
    .export-table-form {
      flex-grow: 1;
      width: 0;
      transition: width .5s;
      display: flex;
      flex-direction: column;
      border: 1px solid #dcdee5;
      border-right: 0;

      @media screen and (max-width: 1366px) {
        max-width: 420px;
      }
      &:hover {
        /* stylelint-disable-next-line declaration-no-important */
        border: 1px solid #c4c6cc !important;
        box-shadow: 0px 3px 6px 0px rgba(0, 0, 0, .1);

        @media screen and (max-width: 1366px) {
          width: 420px;
        }
      }
      .table-title {
        font-size: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #313238;
        min-height: 55px;
        border-bottom: 1px solid #dcdee5;
      }
      .content-none {
        font-size: 14px;
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 166px auto 0;
        i {
          color: #dcdee5;
          font-size: 28px;
          margin-bottom: 13px;
          height: 28px;
        }
      }
      .table-content {
        padding: 4px 0;
        overflow: scroll;
        .content-checkbox {
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 12px;
          .font {
            flex-grow: 1;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
          }
          i {
            color: #3a84ff;
            font-size: 16px;
          }
          .icon {
            margin: 6px -5px 0 0;
            i {
              font-size: 24px;
            }
          }
          .blue {
            color: #3a84ff;
          }
          .gray {
            color: #989dab;
          }
          span {
            color: #c4c6cc;
          }
        }
      }
    }
    .right-border {
      border-right: 1px solid #dcdee5;
    }
    /deep/ .bk-form-checkbox {
      width: 100%;
      padding: 0 15px 0 22px;
      &:hover {
        cursor: pointer;
        background: #eef5ff;
      }
    }
    /deep/ .bk-form-checkbox .bk-checkbox-text {
      width: calc(100% - 22px);
    }
    /deep/ .bk-tooltip-ref {
      margin-top: 2px;
    }
</style>
