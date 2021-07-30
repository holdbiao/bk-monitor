<template>
    <bk-dialog
        :value="value"
        width="480"
        header-position="left"
        :show-footer="false"
        :title="$t('变更记录')"
        @value-change="handleValueChange">
        <ul class="change-record">
            <li class="change-record-item" v-for="(value, key) in labelMap" :key="key">
                <span class="item-label">{{ value }}</span>
                <div class="item-content">{{ recordData[key] || '--'}}</div>
            </li>
        </ul>
    </bk-dialog>
</template>
<script lang="ts">
    import { Prop, Vue, Component, Watch } from 'vue-property-decorator'
    @Component({
        name: 'ChangeRecord'
    })
    export default class ChangeRecord extends Vue {
        value: boolean = false
        labelMap: Object = {}

        @Prop(Object)
        // 更新记录的数据
        recordData: object

        @Prop(Boolean)
        // 是否弹窗
        show: boolean

        @Watch('show', {
            immediate: true
        })
        onShowChange (v) {
            this.value = v
        }

        created () {
            this.labelMap = {
                createUser: this.$t('创建人：'),
                createTime: this.$t('创建时间：'),
                updateUser: this.$t('最后修改人：'),
                updateTime: this.$t('修改时间：')
            }
        }

        // 弹窗状态变更时触发
        handleValueChange (v) {
            this.$emit('update:show', v)
        }
    }
</script>
<style lang="scss" scoped>
    .change-record {
        display: flex;
        flex-direction: column;
        font-size: 14px;
        color: #63656E;
        margin: 3px -24px -26px;
        padding-bottom: 8px;
        &-item {
            display: flex;
            margin-bottom: 20px;
            .item-label {
                flex: 0 0 131px;
                text-align: right;
                color: #979BA5;
            }
            .item-content {
                flex: 1;
                margin-left: 24px;
            }
        }
    }
</style>
