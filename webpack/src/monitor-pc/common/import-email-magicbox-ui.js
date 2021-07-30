import Vue from 'vue'
import { bkLoading,
  bkPopover,  bkClickoutside, bkTooltips, bkOverflowTips
} from 'bk-magic-vue'


// components use
Vue.use(bkPopover)

// directives use
Vue.use(bkClickoutside)
Vue.use(bkTooltips)
Vue.use(bkLoading)
Vue.use(bkOverflowTips)

Vue.prototype.$bkLoading = bkLoading
