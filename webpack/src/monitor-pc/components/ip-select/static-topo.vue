<template>
  <div class="static-topo">
    <bk-big-tree
      ref="tree"
      class="static-topo-content"
      show-checkbox
      :filter-method="handlerSearch"
      :default-checked-nodes="checkedData"
      :default-expanded-nodes="defaultExpanded"
      :data="treeData"
      :height="height"
      @check-change="handleTreeCheck">
    </bk-big-tree>
  </div>
</template>
<script>
import { debounce } from 'throttle-debounce'
import mixin from './topo-mixins'

export default {
  name: 'static-topo',
  mixins: [mixin],
  props: {
    treeData: {
      type: Array,
      required: true
    },
    checkedData: {
      type: Array,
      default() {
        return []
      }
    },
    disabledData: {
      type: Array,
      default() {
        return []
      }
    },
    felterMethod: {
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
      defaultExpanded: []
    }
  },
  watch: {
    treeData: {
      handler(v) {
        this.$refs.tree && this.$refs.tree.setData(v || [])
      }
    },
    checkedData: {
      handler(v, old) {
        const { difference } = this.handlerGetInterOrDiff(v, old)
        this.$refs.tree && this.$refs.tree.setChecked(v, {
          checked: true
        })
        this.$refs.tree && this.$refs.tree.setChecked(difference, {
          checked: old.length === 0
        })
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
    handleTreeCheck(checkedList, node) {
      this.$emit('node-check', 'static-topo', { checked: node.state.checked, data: node.data })
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
        if (Array.isArray(this.defaultExpandNode)) {
          this.defaultExpanded = this.defaultExpandNode
        } else {
          this.defaultExpanded = this.handleGetExpandNodeByDeep(this.defaultExpandNode, this.treeData)
        }
        // this.defaultExpanded.push(this.treeData[0].id)
      }
    }
  }
}
</script>
<style lang="scss" scoped>
    .static-topo {
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
