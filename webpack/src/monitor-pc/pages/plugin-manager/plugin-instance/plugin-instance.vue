<template>
  <div class="plugin-instance-wrapper">
    <div class="plugin-message" v-show="message && left.step === 0 && pluginInfo.type === 'edit'">
      <span class="mo-icon-cc-attribute"></span>
      <div class="text">{{message}}</div>
    </div>
    <div class="plugin-instance">
      <div class="plugin-instance-steps">
        <ul class="step-list">
          <li v-for="(item,index) in left.stepsMap" :key="index" class="step-list-item bk-icon"
              @click="item.done && handleSetStep(index)"
              :class="['step-list-item-' + (index + 1),{ 'is-current': left.step === index,'is-ok': item.done }]">
            <div class="step-list-item-content" :class="{ 'is-current-arrow': left.step === index }">
              {{item.name}}
            </div>
          </li>
        </ul>
      </div>
      <div class="plugin-instance-contaner" ref="pluginContaner">
        <keep-alive>
          <component :show.sync="showView" :is="curStep.component" :data.sync="pluginInfo" :from-route="fromRouteName"></component>
        </keep-alive>
      </div>
    </div>
  </div>
</template>

<script>
import StepSetDone from './set-steps/step-set-done.vue'
import StepSetPlugin from './set-steps/step-set-plugin.vue'
import StepSetTest from './set-steps/step-set-test.vue'
import * as pluginManageAuth from '../authority-map'
import authorityMixinCreate from '../../../mixins/authorityMixin'
import { SET_PLUGIN_CONFIG } from '../../../store/modules/plugin-manager'
import { createNamespacedHelpers } from 'vuex'
const { mapMutations } = createNamespacedHelpers('plugin-manager')

export default {
  name: 'PluginInstance',
  components: {
    StepSetDone,
    StepSetPlugin,
    StepSetTest
  },
  provide() {
    return {
      authority: this.authority,
      handleShowAuthorityDetail: this.handleShowAuthorityDetail,
      pluginManageAuth
    }
  },
  mixins: [authorityMixinCreate(pluginManageAuth)],
  props: {
    show: {
      type: Boolean
    }
  },
  data() {
    return {
      // 缓存上一个路由
      fromRouteName: '',
      pluginInfo: {},
      left: {
        stepsMap: [
          {
            name: this.$t('定义插件'),
            done: false,
            component: 'step-set-plugin'
          },
          {
            name: this.$t('插件调试'),
            done: false,
            component: 'step-set-test'
          },
          {
            name: this.$t('完成'),
            done: false,
            component: 'step-set-done'
          }
        ],
        step: 0
      },
      message: '',
      showView: false,
      right: {

      }
    }
  },
  computed: {
    curStep() {
      return this.left.stepsMap[this.left.step]
    }
  },
  created() {
    const { pluginId } = this.$route.params
    const { params } = this.$route
    const id = params.pluginData ? params.pluginData.plugin_id : ''
    this.$store.commit(
      'app/SET_NAV_TITLE',
      this.$route.name === 'plugin-add' ? this.$t('route-' + '新建插件').replace('route-', '')
        : `${this.$t('route-' + '编辑插件').replace('route-', '')} - ${pluginId || id}`
    )
    this.pluginInfo = {
      isEdit: this.$route.name !== 'plugin-add',
      pluginId,
      type: this.$route.name === 'plugin-add' ? 'create' : 'edit',
      pluginData: params.pluginData
    }
    if (this.pluginInfo.type === 'create' && (pluginId || this.pluginInfo.pluginData)) {
      this.pluginInfo.type = 'import'
    }
    this.showView = this.show
    this.$bus.$on('forward', this.handleForward)
    this.$bus.$on('next', this.handleNextStep)
    this.$bus.$on('showmsg', this.handleShowMsg)
    this.$bus.$on('resetscroll', this.handleScroll)
  },
  beforeDestroy() {
    this.$bus.$off('forward', this.handleForward)
    this.$bus.$off('next', this.handleNextStep)
    this.$bus.$off('showmsg', this.handleShowMsg)
    this.$bus.$on('resetscroll', this.handleScroll)
    this[SET_PLUGIN_CONFIG](null)
  },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      // 缓存上一页过来的路由名字
      vm.fromRouteName = from.name
    })
  },
  async beforeRouteLeave(to, from, next) {
    if (to.name !== 'plugin-add' && to.name !== 'plugin-edit' && this.left.step < 2) {
      const needNext = await this.handleCancel(false)
      next(needNext)
    } else {
      next()
    }
  },
  methods: {
    ...mapMutations([SET_PLUGIN_CONFIG]),
    handleNextStep() {
      const step = this.left.stepsMap[this.left.step]
      if (step) {
        step.done = true
      }
      this.left.step += 1
    },
    // 点击取消
    handleCancel(needBack = true) {
      return new Promise((resolve) => {
        this.$bkInfo({
          title: this.$t('是否放弃本次操作？'),
          confirmFn: () => {
            needBack && this.$router.back()
            resolve(true)
          },
          cancelFn: () => resolve(false)
        })
      })
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
  }
}
</script>

<style scoped lang="scss">
@import "../../home/common/mixins";

.plugin-instance-wrapper {
  .plugin-message {
    background: #f0f8ff;
    height: 42px;
    line-height: 42px;
    border: 1px solid #a3c5fd;
    padding: 0 16px;
    margin-bottom: 16px;
    .mo-icon-cc-attribute {
      font-size: 18px;
      color: #3a84ff;
      vertical-align: sub;
    }
    .text {
      display: inline-block;
      color: #63656e;
      font-size: 14px;
    }
  }
  .plugin-instance {
    display: flex;
    background: #fff;
    box-shadow: 0px 2px 4px 0px rgba(25, 25, 41, .05);
    border-radius: 2px;
    min-height: calc(100vh - 100px);

    @include border-1px();
    &-steps {
      width: 202px;
      // min-height: calc(100vh - 150px);
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
            /* stylelint-disable-next-line declaration-no-important */
            border-left: 1px solid #fafbfd !important;
          }
          &-content {
            font-size: 14px;
            line-height: 19px;
            position: relative;
          }
        }
        .is-ok {
          @include hover();
          &:last-child {
            border-left: 0;
          }
          &:before {
            /* stylelint-disable-next-line declaration-no-important */
            font-size: 28px !important;

            /* stylelint-disable-next-line declaration-no-important */
            content: "\e6b7" !important;

            /* stylelint-disable-next-line declaration-no-important */
            font-family: "icon-monitor" !important;
            background: #dcdee5;
            color: #fff;
            // @include border-1px($primaryFontColor);
            border-color: #dcdee5;
          }
        }
        .is-current {
          color: $primaryFontColor;
          border-left: 1px dashed $primaryFontColor;

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
      // max-height: calc(100vh - 150px);
      flex: 1;
      overflow: auto;
      position: relative;
      &::-webkit-scrollbar {
        width: 4px;
        height: 4px;
      }
    }
  }
}
</style>
