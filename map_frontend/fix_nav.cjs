const fs = require('fs');
const content = fs.readFileSync('frontend/src/components/CommitteeView.vue', 'utf8');

const oldStr = '      <div
' +
  '        v-if="navVisible && isScrollable"
' +
  '        class="fixed right-0 top-1/2 -translate-y-1/2 z-[100]
' +
  '               translate-x-[calc(100%-6px)] hover:translate-x-0
' +
  '               transition-transform duration-300 ease-out
' +
  '               flex items-stretch group"
' +
  '      >';

const newStr = '      <div
' +
  '        v-if="navVisible && isScrollable"
' +
  '        class="fixed right-0 top-1/2 z-[100] flex items-stretch group"
' +
  '        style="transform: translateY(-50%) translateX(calc(100% - 6px)); transition: transform 300ms ease-out;"
' +
  '        @mouseenter="($event.currentTarget as HTMLElement).style.transform = \'translateY(-50%) translateX(0)\'"
' +
  '        @mouseleave="($event.currentTarget as HTMLElement).style.transform = \'translateY(-50%) translateX(calc(100% - 6px))\'"
' +
  '      >';

const idx = content.indexOf(oldStr);
console.log('OLD found at index:', idx);
if (idx !== -1) {
  const updated = content.slice(0, idx) + newStr + content.slice(idx + oldStr.length);
  fs.writeFileSync('frontend/src/components/CommitteeView.vue', updated, 'utf8');
  console.log('Done.');
} else {
  console.log('Not found');
}
