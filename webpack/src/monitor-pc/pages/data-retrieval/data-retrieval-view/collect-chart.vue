<template>
  <div>
    <template v-if="!isSingle">
      <transition name="collection-fade">
        <div class="view-collection" v-show="show">
          <div style="flex-grow: 1;">
            <span>{{ $t('已勾选') }} {{ collectList.length }}/{{ totalCount }} {{ $t('个') }}</span>
            <span class="view-collection-btn" @click="handleCollectionAll">{{ $t('点击全选') }}</span>
            <span class="view-collection-btn" @click="handleShowCollectionDialog">{{ $t('收藏至仪表盘') }}</span>
            <span class="view-collection-btn" v-if="!isDataRetrieval" @click="gotoDataRetrieval">{{ $t('数据检索') }}</span>
            <span class="view-collection-btn mr5" @click="gotoViewDetail">{{ $t('对比大图') }}</span>
          </div>
          <i class="icon-monitor icon-mc-close-fill" @click="handleClose"></i>
        </div>
      </transition>
    </template>

    <!-- 收藏组件 -->
    <collection-dialog
      @on-collection-success="onCollectionSuccess"
      :collection-list="collectList"
      :is-show.sync="isDialogShow">
    </collection-dialog>
  </div>
</template>
<script lang="ts">
import { Vue, Component, Prop, Emit, Watch } from 'vue-property-decorator'
import CollectionDialog from './collection-dialog.vue'

@Component({
  name: 'collect-chart',
  components: {
    CollectionDialog
  }
})
export default class CollectChart extends Vue {
  @Prop({ required: true }) show: boolean
  @Prop({ required: true }) collectList: any[]
  @Prop({ required: true }) totalCount: number
  @Prop({ default: false, type: Boolean }) isSingle: boolean

  isDialogShow = false

  get isDataRetrieval() {
    return this.$route.name === 'data-retrieval'
  }

  @Watch('isDialogShow')
  watchDialogShow(v) {
    if (!v && this.isSingle) {
      this.handleClose()
    }
  }

  @Watch('show', { immediate: true })
  watchShow(v) {
    if (v && this.isSingle) {
      this.handleShowCollectionDialog()
    }
  }
  //
  handleShowCollectionDialog() {
    this.isDialogShow = true
  }

  handleCollectionAll() {
    this.$emit('collect-all')
  }

  onCollectionSuccess() {
    this.handleClose()
  }

  @Emit('close')
  handleClose() {
    return false
  }

  // 跳转数据检索
  @Emit('data-retrieval')
  gotoDataRetrieval() {}

  // 跳转大图
  @Emit('view-detail')
  gotoViewDetail() {}
}
</script>
<style lang="scss" scoped>
@import "../../../static/css/common.scss";

.view-collection {
  display: flex;
  align-items: center;
  position: fixed;
  bottom: 50px;
  left: calc(50vw - 210px);
  height: 42px;
  color: #fff;
  font-size: 14px;
  border: 1px solid #313238;
  background: rgba(0, 0, 0, .85);
  border-radius: 21px;
  padding: 0 11px 0 20px;
  z-index: 1999;
  &-btn {
    margin-left: 10px;
    color: $primaryFontColor;
    cursor: pointer;
  }
  .icon-mc-close-fill {
    font-size: 22px;
    color: #63656e;
    cursor: pointer;
  }
}
.collection-fade-enter-active {
  transition: all .3s ease;
}
.collection-fade-leave-active {
  transition: all .3s ease;
}
.collection-fade-enter,
.collection-fade-leave-to {
  transform: translateY(42px);
  opacity: 0;
}
</style>
