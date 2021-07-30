<template>
  <div v-bkloading="{ isLoading: group.loading }" ref="uptimeCheckTask">
    <group-cards
      ref="groupCards"
      :group="group.data"
      :task-detail.sync="taskDetail"
      @resize="handleWindowResize"
      @drag-drop="handleDragDrop"
      @group-delete="handleGroupDelete"
      @group-edit="handleGroupEdit">
    </group-cards>
    <task-cards
      ref="taskCards"
      v-show="hasSearchData"
      :task-detail.sync="taskDetail"
      v-on="$listeners"
      @delete-task="handleDeleteTask"
      @clone-task="handleCloneTask"
    ></task-cards>
    <div class="empty-search-data" v-show="!hasSearchData">
      <i class="icon-monitor icon-hint"></i> {{ $t('没有搜索到相关拨测任务') }} </div>
  </div>
</template>
<script>
import GroupCards from './group-cards.vue'
import TaskCards from './task-cards.vue'
import { debounce } from 'throttle-debounce'
import { addListener, removeListener } from 'resize-detector'
import { createNamespacedHelpers } from 'vuex'
import { addTaskUptimeCheckGroup, destroyUptimeCheckGroup, createUptimeCheckGroup, updateUptimeCheckGroup,
  destroyUptimeCheckTask, cloneUptimeCheckTask } from '../../../../../monitor-api/modules/model'
const { mapGetters, mapActions } = createNamespacedHelpers('uptime-check-task')
export default {
  name: 'uptime-check-cards',
  components: {
    GroupCards,
    TaskCards
  },
  props: {
    group: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      lisenResize: null,
      taskDetail: {
        show: false,
        tasks: [],
        name: '',
        id: ''
      },
      hasSearchData: true
    }
  },
  computed: {
    ...mapGetters({ keyword: 'keyword', taskList: 'groupTaskList' })
  },
  watch: {
    keyword: {
      handler() {
        setTimeout(() => {
          this.hasSearchData = this.refreshListStatus()
          this.$refs.groupCards.handleGroupChange()
        }, 0)
      }
    },
    taskDetail: {
      handler(v) {
        this.getTaskList({ groupDetail: v.show, tasks: v.tasks })
        this.$emit('change-group-id', v.id)
        this.$emit('change-task-detail', v)
      }
    }
  },
  created() {
    this.lisenResize = debounce(300, v => this.handleWindowResize(v))
  },
  activated() {
    this.handleWindowResize()
  },
  mounted() {
    addListener(this.$refs.uptimeCheckTask, this.lisenResize)
    this.handleWindowResize()
  },
  beforeDestroy() {
    removeListener(this.$refs.uptimeCheckTask, this.lisenResize)
  },
  methods: {
    ...mapActions(['getTaskList']),
    refreshListStatus() {
      if (this.taskDetail.show) {
        return !!this.taskList.length
      }
      return this.$refs.groupCards?.hasGroupList || !!this.taskList.length
    },
    handleDragDrop(id, data) {
      this.$emit('set-loading', true)
      addTaskUptimeCheckGroup(data.id, {
        id: data.id,
        task_id: id
      }).then(() => {
        this.handleUpdateAll()
      })
        .catch(() => {
          this.$emit('set-loading', false)
        })
    },
    async handleWindowResize() {
      await this.$nextTick()
      this.$refs.groupCards && this.$refs.groupCards.refreshItemWidth()
      this.$refs.taskCards && this.$refs.taskCards.refreshItemWidth()
    },
    handleGroupDelete(id) {
      destroyUptimeCheckGroup(id, {}, { needRes: true }).then((res) => {
        this.$bkMessage({
          message: res.result ? this.$t('解散任务组成功') : this.$t('解散任务组失败'),
          theme: res.result ? 'success' : 'error'
        })
        this.handleUpdateAll()
      })
        .catch(() => {
          this.$emit('set-loading', false)
        })
    },
    handleUpdateAll() {
      this.$listeners['update-all']().finally(() => {
        setTimeout(() => {
          this.handleWindowResize()
        }, 50)
      })
    },
    handleGroupEdit(params) {
      this.$emit('set-loading', true)
      const editRes = !params.add
        ? updateUptimeCheckGroup(params.id, params, { needRes: true })
        : createUptimeCheckGroup(params, { needRes: true })
      editRes.then((res) => {
        const success = params.add ? this.$t('创建成功') : this.$t('编辑成功')
        const error = params.add ? this.$t('创建失败') : this.$t('编辑失败')
        this.$bkMessage({
          message: res.result ? success : error,
          theme: res.result ? 'success' : 'error'
        })
        this.handleUpdateAll()
      }).catch(() => {
        this.$emit('set-loading', false)
      })
    },
    handleDeleteTask(item) {
      this.$bkInfo({
        title: this.$t('确认要删除？'),
        maskClose: true,
        confirmFn: () => {
          this.$emit('set-loading', true)
          destroyUptimeCheckTask(item.id, {}, { needRes: true }).then(() => {
            this.$bkMessage({
              theme: 'success',
              message: this.$t('任务删除成功！')
            })
            this.handleUpdateAll()
          })
            .catch(() => {
              this.$emit('set-loading', false)
            })
        }
      })
    },
    // 克隆拨测任务
    handleCloneTask(item) {
      this.$emit('set-loading', true)
      cloneUptimeCheckTask(item.id, {}, { needRes: true }).then(() => {
        this.$bkMessage({
          theme: 'success',
          message: this.$t('任务克隆成功！')
        })
        this.handleUpdateAll()
      })
        .catch(() => {
          this.$emit('set-loading', false)
        })
    }
  }
}
</script>
<style lang="scss" scoped>
    .empty-search-data {
      display: flex;
      height: 42px;
      border: 1px solid #dcdee5;
      background: #fff;
      border-radius: 2px;
      align-items: center;
      justify-content: center;
      color: #63656e;
      font-size: 14px;
      i {
        color: #979ba5;
        font-size: 18px;
        margin-right: 8px;
      }
    }
</style>
