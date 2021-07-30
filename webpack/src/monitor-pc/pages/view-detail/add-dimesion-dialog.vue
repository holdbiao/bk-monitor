<template>
  <monitor-dialog
    :value="isShow"
    :title="$t('添加条件')"
    :before-close="handleBackStep"
    @on-confirm="handleSubmit"
    @on-cancel="handleBackStep">
    <bk-checkbox-group v-model="aaa">
      <bk-checkbox
        class="dialog-checkbox"
        v-for="item in dimensionsList"
        :key="item.id"
        :value="item.id"
        :disabled="item.disabled">
        {{ item.name }}
      </bk-checkbox>
    </bk-checkbox-group>
  </monitor-dialog>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator'
import MonitorDialog from '../../../monitor-ui/monitor-dialog/monitor-dialog.vue'

@Component({
  name: 'add-dimesion-dialog',
  components: {
    MonitorDialog
  }
})
export default class AddDimesionDialog extends Vue {
  @Prop({ default: false })
  isShow: boolean
  @Prop({ default: () => ([]) })
  dimensionsList: any[]
  @Prop({ default: () => ([]) })
  checkedDimensions: []

  aaa = []
  created() {
    this.aaa = this.checkedDimensions
  }
  handleSubmit() {
    const changeList = this.dimensionsList.filter(item => this.aaa.indexOf(item.id) > -1)
    this.$emit('add-dimension', changeList)
    this.$emit('close-dialog', false)
  }

  handleBackStep() {
    this.$emit('close-dialog', false)
  }
}
</script>

<style lang="scss" scoped>
.dialog-checkbox {
  margin-top: 8px;
  padding-right: 16px;
}
</style>
