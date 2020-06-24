---
title: 面试小结
date: 2020-06-24 22:41:24
tags: [前端, 面试]
categories: web
thumbnail: images/interview-summary-1.jpg
disqusId: interview-summary
---

# 算法题

## 全排列

> 实现二维数组的全排列
  ```
  // 如输入[[1,2],[3,4],[5,6]]
  // 输出：
  // [ 1, 3, 5 ]
  // [ 1, 3, 6 ]
  // [ 1, 4, 5 ]
  // [ 1, 4, 6 ]
  // [ 2, 3, 5 ]
  // [ 2, 3, 6 ]
  // [ 2, 4, 5 ]
  // [ 2, 4, 6 ]
  ```

思路：最后需要得到一个二维数组，那基本都是 `reduce` 操作的话也应该是一个二维数组开头，每一次都把前一次结果得到的数组们尾部分别加上二维数组里的一项，也就是 `m * n * [...prevResultList[i], list[j]]`，其中 `m` 和 `n` 分别是 `prevResultList` 和 `list` 的项数，这样也就成功实现了 `m × n` 的项数膨胀，至于降维操作我们有 `flatMap` 这个神器。面试时用了很丑陋的 reduce + map 嵌套，甚至还忘了把数组摊平……

```javascript
function arrange(doubleList) {
  return doubleList.reduce((prevResultList, list) => {
    return prevResultList.flatMap((result) => list.map((v) => result.concat(v)))
  }, [[]])
}
```

## 随机自然数组

> 1~1000 范围内生成长度为 1000 的随机不重复自然数数组，并验证

思路：这道题也是老生常谈了，直接暴力一点 `sort(() => Math.random() > 0.5)` 解之，80% 的面试官都会眼前一愣，心想算了算了投机取巧的家伙，但有一个面试官对此质疑了很久，想了想也是，`sort` 的内部实现并不稳定，而且每次排出来结果不一致不知道性能有没有问题，还是要把随机数稳定下来。

```javascript
function generateRandomInter(n) {
  const list = Array(n).fill(0).map((v, i) => [i + 1, Math.random()])
  list.sort((a, b) => a[1] - b[1])
  return list.map((v) => v[0])
}

function validateResult(result, n) {
  const uniqList = Array.from(new Set(result))
  return uniqList.length === n
}

const result = generateRandomInter(1000)
console.log(result)
console.log(validateResult(result, 1000))
```

## 去重

> 用 es5 实现数组去重？ 
> `[1, 2, 3, true, '2']`

思路：没啥思路，就老老实实遍历再挨个取 `indexOf`？最后面试官给出了 `typeof` 的解法，真是……

```javascript
function unique(list) {
  const cacheMap = {}
  return list.reduce((acc, v) => {
    const key = typeof v + v
    if (cacheMap[key]) {
      return acc
    } else {
      cacheMap[key] = true
      return acc.concat(v)
    }
  }, [])
}
```



## 合并有序数组（链表？）

思路：简单来说维护两个 `head`，每次取一个值插入新数组后就步进一次，然后两者其中一个 `head` 到达底部后一次性将另一个数组剩余元素灌到新数组里。面试官问还有没有高效一点的方案，就用了 `Symbol.iterator` 理论上会高效一点？

```javascript
function mergeList(list1, list2) {
  let result = []
  const iterator1 = list1[Symbol.iterator]()
  const iterator2 = list2[Symbol.iterator]()
  let head1 = iterator1.next()
  let head2 = iterator2.next()
  while (!head1.done && !head2.done) {
    const value1 = head1.value
    const value2 = head2.value
    if (value1 <= value2) {
      result.push(value1)
      head1 = iterator1.next()
    } else {
      result.push(value2)
      head2 = iterator2.next()
    }
  }
  if (!head1.done) {
    result = [...result, head1.value, ...iterator1]
  }
  if (!head2.done) {
    result = [...result, head2.value, ...iterator2]
  }
  return result
}

console.log(mergeList([1, 2], [1, 2, 3]))
```

## 判断二叉树镜像

> 给定一个二叉树，判断是否为镜像
>      1 
>   2     2    
>  3 4   4 3   
>      1
>   2     2
>  3       3 

思路：跟判断两颗二叉树是否相同区别不大，面试时采用了简单粗暴的分层比较法，空间复杂度达到了 `2 ** n` …… 😂

```javascript
function checkMirror(roots) {
  const len = roots.length
  let isAllNull = true
  const doesRootsEqual = roots.every((root, i) => {
    if (root) {
      isAllNull = false
    }
    const oppositeRoot = roots[len - 1 - i]
    return (root && root.val) === (oppositeRoot && oppositeRoot.val)
  })
  if (!doesRootsEqual) { return false }
  if (isAllNull) { return true }
  const nextRoots = roots.flatMap((r) => r ? [r.left, r.right] : [null, null])
  return checkMirror(nextRoots)
}

const root = {
  val: 1,
  left: { val: 2, left: { val: 3}, right: { val: 4, left: { val: 2}}},
  right: { val: 2, left: { val: 4, right: { val: 2}}, right: { val: 3}}
}

console.log(checkMirror([root]))
```

# 工程题

## 控制 Promise 并发

> [promise]
  ```
  dispatch(arr, n) {
      
  }
  ```

思路：肯定要用 `Promise.race`，然后如果要阻塞的话还需要是 `async/await` 写法。这道题其实还是算一般的，后面写个 `Scheduler` 就痛苦了。

```javascript
const promises = Array(10).fill(0).map((v, i) => (
  new Promise((resolve) => setTimeout(() => resolve(i), i * 1000 + 1000)).then(console.log)
))

async function dispatch(list, n) {
  const total = list.length
  let pending = []
  let completed = 0
  while(completed < total && list.length) {
    const moreCount = n - pending.length
    Array(moreCount).fill(0).forEach(() => {
      const p = list.shift()
        .catch(() => {})
        .then(() => pending = pending.filter(v => v !== p))
      pending.push(p)
    })
    console.log('len: ', pending.length)
    await Promise.race(pending)
    completed += 1
  }
}

dispatch(promises, 3)
```


## 实现异步调度器

```typescript
class Scheduler {
    async add(promiseFunc: () => Promise<void>): Promise<void> {
    }
}

const scheduler = new Scheduler()
const timeout = (time) => {
    return new Promise(r => setTimeout(r, time))
}
const addTask = (time, order) => {
    scheduler.add(() => timeout(time))
        .then(() => console.log(order))
}

addTask(1000, 1)
addTask(500, 2)
addTask(300, 3)
addTask(400, 4)
// log: 2 3 1 4
```


思路：一开始看到这题还有些欣喜，似曾相识的感觉，但实际一做发现不是这样，需要直接在 `add` 方法后返回一个 `Promise`，面试时没有写出有效解，事后想想还是能写出个解的，就是实现比较丑陋 ……

```typescript
type promiseFuncType = () => Promise<void>

class Scheduler {
  pending: Array<[promiseFuncType, () => void]>
  running: Array<Promise<void>>
  CONCURRENCY = 2
  constructor() {
    this.pending = []
    this.running = []
  }
  async add(promiseFunc: promiseFuncType): Promise<void> {
    const pending = new Promise<void>((r) => {
      this.pending.push([promiseFunc, r])
    })
    this.execute()
    return pending
  }

  execute = () => {
    let restNum = this.CONCURRENCY - this.running.length
    if (this.running.length === 0 && this.pending.length === 0) {
      return
    }
    while (restNum > 0 && this.pending.length) {
      const [promiseFunc, callback] = this.pending.shift()
      const prom = promiseFunc().then(() => {
        this.running = this.running.filter(p => p !== prom)
        callback()
      })
      this.running.push(prom)
      restNum -= 1
    }
    Promise.race(this.running).then(this.execute)
  }
}

const scheduler = new Scheduler()
const timeout: (number) => Promise<void> = (time) => {
  return new Promise(r => setTimeout(r, time))
}
const addTask = (time, order) => {
  scheduler.add(() => timeout(time))
    .then(() => console.log(order))
}

addTask(1000, 1)
addTask(500, 2)
addTask(300, 3)
addTask(400, 4)
```




## 实现 Observable

思路：观察者和迭代器，需要理解 Observable 和 Observer，才疏学浅，没有 get 到精髓，此题仍为 WIP 状态。

```javascript
const arr = [1, 2, 3]

function Observable() {
  this.uid = 0
  this.subscribers = {}
  this.onSubscribe = null
}

Observable.from = function(array) {
  const observable = new Observable()
  observable.onSubscribe = (observer) => {
    array.forEach((v) => observer.next(v))
    observer.complete()
  }
  return observable
}

Observable.prototype.subscribe = function(observer) {
  const id = this.id++
  this.subscribers[id] = observer
  if (this.onSubscribe) {
    this.onSubscribe(observer)
  }
  return {
    unsubscribe: () => {
      this.subscribers[id] = null
      console.log('unsubscribe')
    }
  }
}
  
const arr$ = Observable.from(arr)

const subscriber = arr$.subscribe({
  next: console.log,
  complete: () => console.log('complete'),
  error: console.error,
})

subscriber.unsubscribe()
```


# 口答知识点

- `HTML` 一点都没问，`CSS` 就问了简单九宫格 header/nav/main 布局以及垂直居中等，说明组件化已经深入人心，高级前端基本没有写样式的部分了
- 简历里写到了 `Gulp/Webpack` 相关，所以被问了很多次 `Webpack Loader/Plugin + Gulp plugin` 开发 😂 像我这么水当然是只能扯扯从一个 `File` 到另一个 `File` 输出这样子的
- `TypeScript` 和 `GraphQL` 也被问了很多次，`TypeScript` 如何实现类型推导（Pick, Omit)，interface 和 type 区别，`GraphQL` 解决什么问题
- `React` 相关：hooks 生命周期，fiber 是啥，setState 到渲染发生了什么 ……
- 深拷贝也是问了无数次，直接 `lodash.cloneDeep` 它不香么 😂 当然有些比如循环引用，class instance 等也是要注意的
- `macroTask/microTask`：一个 macroTask 多个 microTask，microTask-in-microTask 继续排队，Promise((r) => ...) ... 是 macroTask
- `HTTPS` 如何加密通讯过程、Server/Client Hello + 校验证书合法性 + 三次生成随机字符串 + RSA 非对称加密 + 约定密钥对称加密 / 浏览器缓存有哪些字段 / `WebSocket` 做了啥 / `SSO`：在第三方 `Cookie` 无法读取情形下怎么办？（OS：我也很无奈啊）/ `script async defer` 具体怎么 load
- 最复杂、最有挑战性的项目经历：复杂筛选器 + `GraphQL` 应用，小程序解析 nodes 图文混排，原生端通讯 + 跨端开发联调
- 最感兴趣的方向：富文本渲染与编辑、`GIS` 系统以及 `WebAssembly` 相关
