<template>
  <monitor-dialog
    class="dialog-dele-wrapper"
    :value="showDialog"
    :need-header="false"
    :need-footer="false"
    :width="540"
    @change="handleHidden">
    <div class="title-wrapper">
      <i class="icon-monitor icon-mc-delete-line" />
      <div class="title">{{$t('删除采集任务')}}</div>
      <div class="tips">{{$t('需先停用采集任务，也可同时删除关联的策略')}}</div>
    </div>
    <div class="step-wrapper" v-if="!isDeleting">
      <div class="checkbox-wrapper">
        <div class="checkbox-item">
          <bk-checkbox class="checkbox" :checked="!collectTaskIsStop" :disabled="true"></bk-checkbox>
          <span>{{$t('停用该采集任务')}}<span class="tips" v-if="collectorTaskData.status === 'STOPPED'">{{$t('（已停用）')}}</span></span>
        </div>
      </div>
      <div class="checkbox-wrapper">
        <div class="checkbox-item">
          <bk-checkbox
            class="checkbox"
            v-model="checkboxCnofig" :disabled="!hasRelatedStrategy"></bk-checkbox>
          <span class="step-title">{{$t('同时删除相关联的策略配置')}}
            <span v-if="!hasRelatedStrategy" class="tips">{{$t('（未关联策略配置）')}}</span>
            <span v-else class="tips-hl to-detail">
              (
              <span @click="handleGoToStrategyList(listRelatedStrategyFuzzy)">{{$t('有{n}个关联的策略', { n: listRelatedStrategyFuzzy.length })}}</span>
              <!-- <span
                @click="handleGoToStrategyList(listRelatedStrategyFuzzy)"
                v-if="listRelatedStrategyFuzzy.length">{{$t('有{n}个关联的策略配置', { n: listRelatedStrategyFuzzy.length })}}</span>
              <span
                @click="handleGoToStrategyList(listRelatedStrategy)"
                v-if="listRelatedStrategy.length">{{$t(', 有{n}个可能关联的策略', { n: listRelatedStrategy.length })}}</span> -->
              <i class="icon-monitor icon-mc-wailian" /> )
            </span>
          </span>
        </div>
        <div class="tips tips1">{{$t('若不同时删除掉，相关联的策略配置则会成为失效策略')}}</div>
      </div>
    </div>
    <div class="running-wrapper" v-else-if="deletingStepList.length">
      <div
        class="step-item"
        v-for="(item, index) in deletingStepList"
        :key="index">
        <div class="header">
          <img v-if="item.loading" class="loading" src="../../../static/images/svg/spinner.svg" alt="">
          <div v-else class="poit"></div>
          <div class="title">{{item.title}}</div>
        </div>
        <div
          class="tips"
          v-if="item.data">
          <span>{{$t('已停用')}}</span>
          <span class="tips-hl">{{item.data.node}}</span>
          <span>{{$t('个节点内的')}}</span>
          <span class="tips-hl">{{item.data.total}}</span>
          <span>{{$t('台主机')}}</span>
          <span class="tips-hl to-detail" @click="handleCheckStatus">（{{$t('查看详情')}} <i class="icon-monitor icon-mc-wailian" />）</span>
        </div>
        <div :class="['line', { 'need-line': deletingStepList[index + 1], 'is-loading': item.loading }]"></div>
      </div>
    </div>
    <div class="del-btn-wrapper">
      <bk-button
        class="del-btn"
        :theme="'primary'"
        :disabled="isDeleting && !isDeleted"
        @click="handleDel">{{isDeleted ? $t('删除完成') : (isDeleting ? $t('删除中...') : $t('删除'))}}</bk-button>
    </div>
  </monitor-dialog>
</template>

<script lang='ts'>
import { Vue, Component, Prop, Watch, PropSync } from 'vue-property-decorator'
import { ICollectorTaskData, IDeletingStepListItem } from '../collector-type'
import { listRelatedStrategy,
  collectTargetStatus,
  toggleCollectConfigStatus,
  deleteCollectConfig } from '../../../../monitor-api/modules/collecting'
import { deleteStrategyConfig } from '../../../../monitor-api/modules/strategies'
import monitorDialog from '../../../../monitor-ui/monitor-dialog/monitor-dialog.vue'

// 删除采集配置弹层
@Component({
  name: 'collector-dialog-delete',
  components: {
    monitorDialog
  }
})
export default class DeleteCollector extends Vue {
  // 显示状态
  @PropSync('show', { type: Boolean, default: false }) showDialog: boolean
  // 采集任务状态数据
  @Prop({ required: true, type: Object, default: () => ({}) }) collectorTaskData: ICollectorTaskData

  // 是否停用采集任务
  //   private checkboxTask = true
  // 是否删除相关策略
  private checkboxCnofig = false
  private loading = false
  // 精准关联的策略
  private listRelatedStrategy: any = []
  // 模糊关联的策略
  private listRelatedStrategyFuzzy: any = []

  // 删除中
  private isDeleting = false

  // 已删除采集任务状态
  private isDeleted = false

  private deletingStepList: IDeletingStepListItem[] = []
  // 采集任务是否已停用
  get collectTaskIsStop(): boolean {
    return this.collectorTaskData.status === 'STOPPED'
  }
  // 有关联的策略
  get hasRelatedStrategy(): boolean {
    return this.listRelatedStrategy.length > 0 || this.listRelatedStrategyFuzzy.length > 0
  }

  @Watch('show')
  handleShow(v: boolean) {
    if (v) {
      this.deletingStepList = []
      this.isDeleted = false
      this.isDeleting = false
      this.getCollectorConifg()
    } else {
      this.checkboxCnofig = false
    }
  }

  // 获取关联的策略配置
  async getCollectorConifg() {
    this.loading = true
    const res = await listRelatedStrategy({ collect_config_id: this.collectorTaskData.id })
      .catch(() => null)
      .finally(() => (this.loading = false))
    this.listRelatedStrategy = res ? res.accurate_strategies : []
    this.listRelatedStrategyFuzzy = res ? res.fuzzy_strategies : []
  }
  handleHidden() {
    this.showDialog = false
  }

  // 删除操作
  async handleDel() {
    if (this.isDeleted) {
      this.showDialog = false
      return
    }
    this.isDeleting = true
    this.handleStepList()
    if (!this.collectTaskIsStop) {
      // 1、停用主机请求
      const res = await toggleCollectConfigStatus({ id: this.collectorTaskData.id, action: 'disable' })
      if (!res) return
      if (!this.showDialog) return
      // 2、轮训主机停用状态
      await this.pollingStatus()
    }

    if (this.hasRelatedStrategy && this.checkboxCnofig) {
      if (!this.showDialog) return
      // 3、删除关联策略
      let ids = this.listRelatedStrategy.map(item => item.strategy_id)
      ids = [...ids, ...this.listRelatedStrategyFuzzy.map(item => item.strategy_id)]
      ids = [...new Set(ids)]
      const strategy = this.deletingStepList.find(item => item.type === 'strategy')
      strategy.loading = true
      await deleteStrategyConfig({ ids }).catch(e => e)
        .finally(() => {
          strategy.loading = false
        })
    }
    if (!this.showDialog) return
    // 4、删除采集任务
    await deleteCollectConfig({ id: this.collectorTaskData.id }).then(() => {
      this.isDeleted = true
    })
  }

  // 轮训停用状态
  pollingStatus() {
    return new Promise((resolve) => {
      const polling = () => {
        const timer = setTimeout(() => {
          clearTimeout(timer)
          const collect = this.deletingStepList[0]
          if (collect.loading) {
            this.getHosts().then((data: any) => {
              collect.data.total = data.contents.reduce((total, item) => [...total, ...item.child], [])
                .filter(item => item.status === 'SUCCESS').length
              collect.data.node = data.contents.length
            })
              .finally(() => {
                this.showDialog && polling()
              })
          } else {
            collect.title = this.$tc('采集任务已停用')
            resolve('ok')
          }
        }, 3000)
      }
      polling()
    })
  }

  // 生成删除步骤数据
  handleStepList() {
    // 策略未停用
    if (!this.collectTaskIsStop) {
      this.deletingStepList.push({
        type: 'collect',
        loading: true,
        title: this.$tc('采集任务正在停用中…'),
        data: {
          total: 0,
          node: 0
        }
      })
    }
    // 有关联策略
    if (this.hasRelatedStrategy && this.checkboxCnofig) {
      this.deletingStepList.push({
        type: 'strategy',
        loading: false,
        title: this.$tc('删除相关联的策略配置')
      })
    }
  }

  // 查询主机状态
  getHosts(id = this.collectorTaskData.id) {
    return new Promise((resolve, reject) => {
      collectTargetStatus({ id }).then((data) => {
        const collect = this.deletingStepList.find(item => item.type === 'collect')
        const hasRunning = data.contents.some(item => item.child.some(set => (set.status === 'RUNNING'
          || set.status === 'PENDING')))
        if (collect) {
          collect.loading = hasRunning
        }
        resolve(data)
      })
        .catch((err) => {
          reject(err)
        })
    })
  }

  handleCheckStatus() {
    if (!this.collectTaskIsStop) {
      this.$router.push({
        name: 'collect-config-operate-detail',
        params: {
          id: `${this.collectorTaskData.id}`,
          title: this.collectorTaskData.name
        }
      })
    }
  }

  handleGoToStrategyList(list: any) {
    const ids = list.map(item => item.strategy_id)
    this.$router.push({
      name: 'strategy-config',
      params: {
        bkStrategyId: ids.map(item => ({
          id: `${item}`,
          name: item
        }))
      }
    })
  }
}
</script>

<style lang="scss" scoped>
.dialog-dele-wrapper {
  /deep/.monitor-dialog {
    /* stylelint-disable-next-line declaration-no-important */
    padding-bottom: 24px !important;
  }
  .title-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 22px ;
    .icon-mc-delete-line {
      display: flex;
      justify-content: center;
      align-items: center;
      width: 52px;
      height: 52px;
      font-size: 52px;
      margin-bottom: 22px;
    }
    .title {
      color: #313238;
      line-height: 28px;
      font-size: 20px;
      margin-bottom: 4px;
    }
    .tips {
      font-size: 12px;
      line-height: 20px;
      color: #63656e;;
    }
  }
  .step-wrapper,
  .running-wrapper {
    padding: 17px 16px;
    margin-top: 24px;
    background-color: #f5f6fa;
    .checkbox-wrapper {
      font-size: 12px;
      color: #63656e;
      &:not(:last-child) {
        margin-bottom: 12px;
      }
      .checkbox-item {
        display: flex;
        align-items: center;
        height: 20px;
        .step-title {
          display: flex;
          align-items: center;
          .tips {
            white-space: nowrap;
          }
        }
        .checkbox {
          margin-right: 8px;
          overflow: visible;
        }
      }
      .tips {
        color: #c4c6cc;
      }
      .tips1 {
        padding-left: 24px;
        line-height: 20px;
      }
    }
  }
  .running-wrapper {
    .step-item {
      position: relative;
      .header {
        position: relative;
        padding-left: 21px;
        .loading {
          position: absolute;
          top: 0;
          left: 0;
          display: inline-block;
          width: 16px;
          height: 16px;
        }
        .poit {
          position: absolute;
          top: 5px;
          left: 5px;
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background-color: #c4c6cc;
        }
        .title {
          line-height: 16px;
          font-size: 12px;
          color: #63656e;
        }
      }
      .tips {
        display: flex;
        align-items: center;
        line-height: 16px;
        font-size: 12px;
        color: #63656e;
        margin-top: 3px;
        padding-bottom: 13px;
        padding-left: 21px;
      }
      .line {
        display: none;
        position: absolute;
        left: 7px;
        top: 13px;
        width: 2px;
        height: calc(100% - 9px);
        background: #dcdee5;
      }
      .need-line {
        display: block;
      }
      .is-loading {
        top: 17px;
        height: calc(100% - 14px);
      }
    }
  }
  .tips-hl {
    white-space: nowrap;
    color: #3a84ff;
    .icon-mc-wailian {
      font-size: 16px;
    }
  }
  .to-detail {
    display: flex;
    align-items: center;
    cursor: pointer;
  }
  .del-btn-wrapper {
    .del-btn {
      display: block;
      width: 180px;
      margin: 0 auto;
      margin-top: 20px;
    }
    /deep/.is-disabled {
      background-color: #c3daff;
      border-color: #c3daff;
    }
  }

}
</style>
