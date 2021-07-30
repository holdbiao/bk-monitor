import Vue from 'vue'
import {
  bkButton, bkCheckbox, bkCheckboxGroup, bkCol, bkCollapse, bkCollapseItem, bkContainer, bkDatePicker,
  bkDialog, bkDropdownMenu, bkException, bkForm, bkFormItem, bkInfoBox, bkInput, bkLoading, bkMessage,
  bkNavigation, bkNavigationMenu, bkNavigationMenuItem, bkNavigationMenuGroup, bkNotify, bkOption, bkOptionGroup,
  bkPagination,
  bkPopover, bkProcess, bkProgress, bkRadio, bkRadioGroup, bkRoundProgress, bkRow, bkSearchSelect, bkSelect,
  bkSideslider, bkSlider, bkSteps, bkSwitcher, bkTab, bkTabPanel, bkTable, bkTableColumn, bkTagInput, bkTimePicker,
  bkTimeline, bkTree, bkClickoutside, bkTooltips, bkBigTree, bkOverflowTips, bkCascade, bkVirtualScroll, bkAlert, bkBadge
} from 'bk-magic-vue'
// import { Select, Option } from 'element-ui'
// Vue.use(Select)
// Vue.use(Option)
// bkDiff 组件体积较大且不是很常用，因此注释掉。如果需要，打开注释即可
// import { bkDiff } from '@tencent/bk-magic-vue'

// components use
Vue.use(bkBadge)
Vue.use(bkButton)
Vue.use(bkCheckbox)
Vue.use(bkCheckboxGroup)
Vue.use(bkCol)
Vue.use(bkCollapse)
Vue.use(bkCollapseItem)
Vue.use(bkContainer)
Vue.use(bkDatePicker)
Vue.use(bkDialog)
Vue.use(bkDropdownMenu)
Vue.use(bkException)
Vue.use(bkForm)
Vue.use(bkFormItem)
Vue.use(bkInput)
// Vue.use(bkMemberSelector)
Vue.use(bkNavigation)
Vue.use(bkNavigationMenu)
Vue.use(bkNavigationMenuItem)
Vue.use(bkNavigationMenuGroup)
Vue.use(bkOption)
Vue.use(bkOptionGroup)
Vue.use(bkPagination)
Vue.use(bkPopover)
Vue.use(bkProcess)
Vue.use(bkProgress)
Vue.use(bkRadio)
Vue.use(bkRadioGroup)
Vue.use(bkRoundProgress)
Vue.use(bkRow)
Vue.use(bkSearchSelect)
Vue.use(bkSelect)
Vue.use(bkSideslider)
Vue.use(bkSlider)
Vue.use(bkSteps)
Vue.use(bkSwitcher)
Vue.use(bkTab)
Vue.use(bkTabPanel)
Vue.use(bkTable)
Vue.use(bkTableColumn)
Vue.use(bkTagInput)
Vue.use(bkTimePicker)
Vue.use(bkTimeline)
// Vue.use(bkTransfer)
Vue.use(bkTree)
// Vue.use(bkUpload)
Vue.use(bkBigTree)
Vue.use(bkCascade)
Vue.use(bkVirtualScroll)

// directives use
Vue.use(bkClickoutside)
Vue.use(bkTooltips)
Vue.use(bkLoading)
Vue.use(bkOverflowTips)
Vue.use(bkAlert)

// Vue prototype mount
Vue.prototype.$bkInfo = bkInfoBox
Vue.prototype.$bkMessage = bkMessage
Vue.prototype.$bkNotify = bkNotify
Vue.prototype.$bkLoading = bkLoading
