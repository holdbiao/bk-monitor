<template>
  <div class="add-del-wrapper" v-bkloading="{ 'isLoading': pageLoading }">
    <div class="add-del">
      <div class="add-del-steps">
        <ul class="step-list">
          <li v-for="(item,index) in left.stepsMap" :key="index" class="step-list-item"
              @click="item.done && handleSetStep(index)"
              :class="['step-list-item-' + (index + 1),{ 'is-current': left.step === index,'is-ok': item.done }]">
            <div class="step-list-item-content" :class="{ 'is-current-arrow': left.step === index }">
              {{item.name}}
            </div>
          </li>
        </ul>
      </div>
      <div class="add-del-contaner" ref="pluginContaner">
        <keep-alive>
          <component
            @refresh="handleRefresh"
            @step-change="handleStepChange"
            @target="targetUpdata"
            :data="data"
            :page-loading.sync="pageLoading"
            :hosts.sync="hosts"
            :step.sync="left.step"
            :type.sync="componentType"
            :need-rollback.sync="needRollback"
            :is="curStep.component"
            :config="config"
            :diff-data.sync="diffData"
            :target="target">
          </component>
        </keep-alive>
      </div>
    </div>
  </div>
</template>

<script>
import BkHost from './bk-host/bk-host'
import TargetTable from './target-table/target-table'
import Done from './add-del-done/add-del-done'
import { collectConfigDetail } from '../../../../monitor-api/modules/collecting'
export default {
  name: 'AddAndDel',
  components: {
    BkHost,
    TargetTable,
    Done
  },
  data() {
    return {
      componentName: 'add-and-del',
      config: {
        params: {},
        set: {
          data: {},
          others: {}
        }
      },
      hosts: {},
      diffData: {},
      left: {
        stepsMap: [
          {
            name: this.$t('选择目标'),
            done: false,
            component: 'bk-host'
          },
          {
            name: this.$t('采集下发'),
            done: false,
            component: 'TargetTable'
          },
          {
            name: this.$t('完成'),
            done: false,
            component: 'done'
          }
        ],
        step: 0
      },
      pageLoading: true,
      ipLoading: true,
      version: '',
      componentType: 'ADD_DEL',
      needRollback: true,
      target: {}
    }
  },
  computed: {
    curStep() {
      return this.left.stepsMap[this.left.step]
    }
  },
  created() {
    this.data = this.$route.params.data
    this.$store.commit('app/SET_NAV_TITLE', this.$t('加载中...'))
  },
  mounted() {
    this.getCollectorConfigDetail()
    this.left.step = 0
    this.version = `${this.data.updateParams.configVersion}.${this.data.updateParams.infoVersion}`
  },
  methods: {
    handleStepChange(v, index) {
      this.left.stepsMap[index].done = v
    },
    handleNextStep() {
      this.left.stepsMap[this.left.step].done = true
      this.left.step += 1
    },
    handleShowMsg(msg) {
      this.message = msg
    },
    handleRefresh() {
      this.pageLoading = false
    },
    handleForward() {
      this.left.step -= 1
    },
    handleSetStep(index) {
      if (this.left.stepsMap[index].done) {
        return
      }
      this.left.step = index
    },
    handleStepOk(v) {
      this.curStep.done = v
    },
    handleScroll() {
      if (this.$refs.pluginContaner) {
        this.$refs.pluginContaner.scrollTop = 0
      }
    },
    getConfigParams(data) {
      this.config.id = data.id
      this.config.mode = 'edit'
      this.config.set.data.objectType = this.data.objectTypeEn
      this.config.set.others.targetNodeType = this.data.nodeType
      this.config.set.others.targetNodes = data.collect_type === 'SNMP'
        ? data.target_nodes
        : data.target || data.target_nodes
      this.config.set.others.remoteCollectingHost = data.remote_collecting_host
      this.config.supportRemote = data.plugin_info.is_support_remote
      this.config.params = {
        name: data.name,
        collect_type: data.collect_type,
        target_object_type: data.target_object_type,
        target_node_type: data.target_node_type,
        plugin_id: data.plugin_info.plugin_id,
        target_nodes: data.target || data.target_nodes,
        params: data.params,
        label: data.label,
        remote_collecting_host: data.remote_collecting_host
      }
      this.$store.commit(
        'app/SET_NAV_TITLE',
        `${this.$t('route-' + '增删目标').replace('route-', '')} - #${data.id} ${data.name}`
      )
      this.config.target = {}
    },
    getCollectorConfigDetail() {
      this.pageLoading = true
      collectConfigDetail({ id: this.data.id }).then((data) => {
        this.getConfigParams(data)
      })
    },
    targetUpdata(v) {
      this.target = v
    }
  }
}
</script>

<style scoped lang="scss">
@import "../../home/common/mixins";

.add-del-wrapper {
  .add-del {
    display: flex;
    background: #fff;
    box-shadow: 0px 2px 4px 0px rgba(25, 25, 41, .05);
    border-radius: 2px;

    @include border-1px();
    &-steps {
      width: 202px;
      height: calc(100vh - 110px);
      background: $defaultBgColor;
      border-radius: 2px 0px 0px 0px;
      border-right: 1px solid $defaultBorderColor;
      .step-list {
        margin-left: 45px;
        padding: 40px 0 0 0;

        @for $i from 1 through 7 {
          &-item-#{$i} {
            &:before {
              content: "#{$i}";
            }
          }
        }
        &-item {
          position: relative;
          border-left: 1px dashed $defaultBorderColor;
          height: 70px;
          padding-left: 25px;
          color: $defaultFontColor;
          &:before {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            text-align: center;
            line-height: 26px;
            background: #fff;
            // box-shadow: 0px 2px 4px 0px rgba(0, 130, 255, 0.15);
            color: $defaultFontColor;
            display: inline-block;
            position: absolute;
            left: -15px;
            top: -5px;

            @include border-1px(#C4C6CC);
          }
          &:last-child {
            border-left: 0;
          }
          &-content {
            font-size: 14px;
            line-height: 19px;
            position: relative;
          }
        }
        .is-ok {
          border-left: 1px dashed #dcdee5;

          @include hover();
          &:last-child {
            border-left: 0;
          }
          &:before {
            /* stylelint-disable-next-line declaration-no-important */
            font-size: 18px !important;

            /* stylelint-disable-next-line declaration-no-important */
            content: "\e6b7" !important;

            /* stylelint-disable-next-line declaration-no-important */
            font-family: "icon-monitor" !important;
            background: #dcdee5;
            color: #fff;
            border: 1px solid #dcdee5;
          }
        }
        .is-current {
          color: $primaryFontColor;

          @include hover();
          &:before {
            color: #fff;
            background: $primaryFontColor;

            @include border-1px($primaryFontColor);
          }
          &-arrow {
            &:after {
              content: "";
              position: absolute;
              right: -6px;
              top: 3px;
              width: 10px;
              height: 10px;
              border-left: 1px solid $defaultBorderColor;
              border-top: 1px solid $defaultBorderColor;
              transform: rotate(-45deg);
              background: #fff;
            }
          }
        }
      }
    }
    &-contaner {
      max-height: calc(100vh - 110px);
      flex: 1;
      overflow: auto;
      position: relative;
      &::-webkit-scrollbar {
        width: 2px;
        height: 2px;
      }
    }
  }
}
</style>
