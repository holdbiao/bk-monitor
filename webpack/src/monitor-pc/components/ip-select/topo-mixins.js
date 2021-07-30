export default {
  props: {
    defaultExpandNode: {
      type: [Array, Number], // Array类型：需要展开节点的ID, String类型：展开层次
      default() {
        return 1
      },
      validator(value) {
        if (typeof value === 'number') {
          return value > 0
        }
        return true
      }
    }
  },
  methods: {
    handleGetExpandNodeByDeep(deep = 1, treeData = []) {
      return treeData.reduce((pre, node) => {
        ((deep) => {
          if (deep > 1 && Array.isArray(node.children) && node.children.length > 0) {
            // eslint-disable-next-line no-param-reassign
            deep -= 1
            // eslint-disable-next-line no-param-reassign
            pre = pre.concat(this.handleGetExpandNodeByDeep(deep, node.children))
          } else {
            // eslint-disable-next-line no-param-reassign
            pre = pre.concat(node.id)
          }
        })(deep)
        return pre
      }, [])
    },
    resize() {
      this.$refs.tree && this.$refs.tree.resize()
    }
  }
}
