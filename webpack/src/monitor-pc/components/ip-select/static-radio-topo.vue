<template>
  <section class="static-topo-radio">
    <bk-radio-group v-model="checkedIp">
      <bk-big-tree
        ref="tree"
        :check-strictly="false"
        :data="treeData"
        :filter-method="handlerSearch"
        :default-checked-nodes="checkedData"
        :default-expanded-nodes="defaultExpanded"
        :height="height">
        <template #default="{ node, data }">
          <bk-radio v-if="data && data.ip"
                    :value="`${data.ip}|${data.bk_cloud_id}`"
                    @change="selectChange(data)">
            {{ node.name }}
          </bk-radio>
          <span v-else>
            {{ node ? node.name : '' }}
          </span>
        </template>
      </bk-big-tree>
    </bk-radio-group>
  </section>
</template>
<script>
import { debounce } from 'throttle-debounce'
import mixin from './topo-mixins'

export default {
  name: 'static-radio-topo',
  mixins: [mixin],
  props: {
    treeData: {
      type: Array,
      required: true
    },
    // 单选项
    checkedData: {
      type: Array,
      default() {
        return []
      },
      validator(value) {
        return value.length <= 1
      }
    },
    disabledData: {
      type: Array,
      default() {
        return []
      }
    },
    filterMethod: {
      type: Function,
      default: () => () => {}
    },
    keyword: {
      type: String,
      default: ''
    },
    isSearchNoData: Boolean,
    height: Number
  },
  data() {
    return {
      watchKeword: null,
      defaultExpanded: [],
      checkedIp: '',
      checkedNodeData: null
    }
  },
  watch: {
    treeData: {
      handler(v) {
        this.$refs.tree && this.$refs.tree.setData(v || [])
      }
    },
    checkedData: {
      handler(v) {
        if (v.length === 0) {
          this.checkedIp = ''
          this.checkedNodeData = null
        } else {
          this.checkedIp = v[0] ? `${v[0].ip}|${v[0].bkCloudId}` : ''
        }
      }
    },
    disabledData: {
      handler(v, old) {
        const { difference } = this.handlerGetInterOrDiff(v, old)
        this.$refs.tree && this.$refs.tree.setDisabled(v, {
          disabled: true
        })
        this.$refs.tree && this.$refs.tree.setDisabled(difference, {
          disabled: old.length === 0
        })
      }
    },
    checkedIp: {
      handler(v) {
        if (v) {
          this.handleTreeCheck(Boolean(v), this.checkedNodeData)
        }
      }
    }
  },
  created() {
    this.watchKeword = this.$watch('keyword', debounce(300, this.handleFilter))
    this.handleDefaultExpanded()
  },
  mounted() {
    if (this.keyword.length) {
      this.handleFilter(this.keyword)
    }
  },
  beforeDestory() {
    this.watchKeword && this.watchKeword()
  },
  methods: {
    handleTreeCheck(checked = false, data = {}) {
      this.$emit('node-check', 'static-topo-radio', { checked, data })
    },
    handleFilter(v) {
      const data = this.$refs.tree.filter(v)
      this.$emit('update:isSearchNoData', !data.length)
    },
    handlerSearch(keyword, node) {
      return (`${node.data.ip}`).indexOf(keyword) > -1 || (`${node.data.name}`).indexOf(keyword) > -1
    },
    handlerGetInterOrDiff(v, old) {
      const intersection = v.filter(item => old.indexOf(item) > -1)
      let difference = v.filter(item => old.indexOf(item) === -1).concat(old.filter(item => v.indexOf(item) === -1))
      difference = difference.filter(set => !~v.indexOf(set))
      return { intersection, difference }
    },
    handleDefaultExpanded() {
      if (this.checkedData.length) {
        // 回显数据
        this.defaultExpanded = this.checkedData
      } else {
        // 默认展开树
        Array.isArray(this.defaultExpandNode)
          ? this.defaultExpanded = this.defaultExpandNode
          : this.defaultExpanded = this.handleGetExpandNodeByDeep(this.defaultExpandNode, this.treeData)
      }
    },
    selectChange(data) {
      this.checkedNodeData = data
    }
  }
}
</script>
<style lang="scss" scoped>
    .static-topo-radio {
      padding-top: 15px;
      /deep/ .bk-big-tree {
        .node-content {
          overflow: inherit;
          text-overflow: inherit;
          white-space: nowrap;
          font-size: 14px;
        }
      }
    }
</style>
