<template>
  <div class="stop-start-wrapper" v-bkloading="{ 'isLoading': pageLoading }">
    <div class="stop-start">
      <div class="stop-start-steps">
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
      <div class="stop-start-contaner" ref="pluginContaner" v-if="initDone">
        <keep-alive>
          <component
            @refresh="handleRefresh"
            :step.sync="left.step"
            :is="curStep.component"
            :type.sync="type"
            :hosts.sync="hosts"
            :data="data"
            :open-detail="openDetail"
            :diff-data.sync="diffData"
            :upgrade-params="upgradeParams"></component>
        </keep-alive>
      </div>
    </div>
  </div>
</template>

<script>
import AddDel from '../collector-target-add-del/target-table/target-table'
import AddDelDone from '../collector-target-add-del/add-del-done/add-del-done'
import StopStart from './stop-start-host/stop-start-host'
import StopDone from './stop-done/stop-done'
export default {
  name: 'StopStartView',
  components: {
    StopStart,
    StopDone,
    AddDel,
    AddDelDone
  },
  // props: {
  //     data: {
  //         type: Object,
  //         default: () => {}
  //     },
  //     stopStart: {
  //         type: Object,
  //         default: () => ({})
  //     }
  // },
  data() {
    return {
      hosts: {},
      configInfo: {},
      type: '',
      isRefreshConfigList: false,
      operationType: 'START',
      openDetail: false,
      upgradeParams: {},
      left: {
        stepsMap: [
          {
            name: this.$t('采集下发'),
            done: true,
            component: 'stop-start'
          },
          {
            name: this.$t('完成'),
            done: false,
            component: 'stop-done'
          }
        ],
        step: 0
      },
      diffData: {},
      initDone: false,
      version: '',
      pageLoading: true
    }
  },
  computed: {
    curStep() {
      return this.left.stepsMap[this.left.step]
    },
    data() {
      return this.$route.params.data
    },
    stopStart() {
      return this.$route.params.stopStart
    }
  },
  beforeDestroy() {
    if (this.operationCount) {
      this.$parent.handleGetListData()
    }
  },
  async created() {
    this.pageLoading = true
    this.$store.commit(
      'app/SET_NAV_TITLE',
      `${this.$route.params.title} - #${this.$route.params.data.id} ${this.$route.params.data.name}`
    )
    this.configInfo = this.data
    this.type = this.stopStart.type
    this.upgradeParams = this.stopStart.params
    this.initDone = true
  },
  methods: {
    handleNextStep() {
      this.left.stepsMap[this.left.step].done = true
      this.left.step += 1
    },
    handleRefresh() {
      this.pageLoading = false
    },
    handleShowMsg(msg) {
      this.message = msg
    },
    handleForward() {
      this.left.step -= 1
    },
    handleSetStep(index) {
      this.left.step = index
    },
    handleStepOk(v) {
      this.curStep.done = v
    },
    handleScroll() {
      if (this.$refs.pluginContaner) {
        this.$refs.pluginContaner.scrollTop = 0
      }
    }
    // getUpOperation(id) {
    //   return configOperationInfo({ id })
    // },
    // addProp(obj) {
    //   const status = {
    //     START: 'STOPPED',
    //     STOP: 'STARTED'
    //   }
    //   this.data.id = obj.id
    //   this.data.name = obj.name
    //   this.data.updateParams = {}
    //   this.data.updateParams.configVersion = obj.config_version
    //   this.data.updateParams.infoVersion = obj.info_version
    //   this.data.objectTypeEn = obj.target_object_type
    //   this.data.status = obj.status
    //   this.data.nodeType = obj.target_node_type
    //   this.data.allowRollback = obj.allow_rollback
    //   this.type = status[obj.last_operation] || obj.last_operation
    //   this.operationType = obj.last_operation
    // }
    // getDiffData() {
    //   return deploymentConfigDiff({ id: this.data.id })
    // },
    // getAutoDeploy() {
    //   autoCollectStatus({ id: this.data.id }).then((data) => {
    //     this.diffData = data.diff_node
    //   })
    // }
    // handleUpgrade () {
    //     this.$parent.handleCloseUpdate(true)
    // }
  }
}
</script>

<style scoped lang="scss">
@import "../../home/common/mixins";

.stop-start-wrapper {
  .stop-start {
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
            width: 28px;
            height: 28px;
            border-radius: 50%;
            text-align: center;
            line-height: 28px;
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
          border-left: 1px dashed $primaryFontColor;

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
            color: #fff;
            background: #dcdee5;
            border: 1px solid #c4c6cc;
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
