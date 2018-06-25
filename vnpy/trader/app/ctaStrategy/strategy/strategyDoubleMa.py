# encoding: UTF-8

"""
这里的Demo是一个最简单的双均线策略实现
"""

from __future__ import division

from vnpy.trader.vtConstant import EMPTY_STRING, EMPTY_FLOAT
from vnpy.trader.app.ctaStrategy.ctaTemplate import (CtaTemplate, 
                                                     BarGenerator,
                                                     ArrayManager)


########################################################################
class DoubleMaStrategy(CtaTemplate):
    """双指数均线策略Demo"""
    className = 'DoubleMaStrategy'
    author = u'DYTGo'
    
    # 策略参数
    fastWindow = 1    # 快速均线参数
    md1Window=5      #中速均线参数1
    md2Window=10     #中速均线参数2
    slowWindow = 30   # 慢速均线参数
    offsetWindow=60     #偏移值窗口（收盘价-最低价）/（最高价-最低价）
    threshold=0.5      #偏移阈值
    initDays = 0      # 初始化数据所用的天数
    fixedSize=1       #每次交易的数量
    stopPoint=50        #固定止损点
    
    # 策略变量
    fastMa0 = EMPTY_FLOAT   # 当前最新的快速EMA
    fastMa1 = EMPTY_FLOAT   # 上一根的快速EMA
    
    slowMa0 = EMPTY_FLOAT  # 当前最新的慢速EMA
    slowMa1 = EMPTY_FLOAT  # 上一根的慢速EMA
    
    md1MA0=EMPTY_FLOAT    #当前最新的中速EMA1
    md2MA0=EMPTY_FLOAT    #当前最新的中速EMA2
    
    offsetValue=EMPTY_FLOAT  #当前最新的偏移值
    
    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'fastWindow',
                 'slowWindow',
                 'md1Window',
                 'md2Window',
                 'offsetWindow',
                 'threshold',
                 'fixedSize',                
                 'stopPoint']    
    
    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'fastMa0',
               'fastMa1',
               'slowMa0',
               'slowMa1',
               'md1MA0',
               'md2MA0',
               'offsetValue',
               ]  
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(DoubleMaStrategy, self).__init__(ctaEngine, setting)
        
        self.bg = BarGenerator(self.onBar)
        self.am = ArrayManager()
        
        # 注意策略类中的可变对象属性（通常是list和dict等），在策略初始化时需要重新创建，
        # 否则会出现多个策略实例之间数据共享的情况，有可能导致潜在的策略逻辑错误风险，
        # 策略类中的这些可变对象属性可以选择不写，全都放在__init__下面，写主要是为了阅读
        # 策略时方便（更多是个编程习惯的选择）
        
    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'MA组合演示策略初始化')
        
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)
        
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'MA组合演示策略初始化')
        self.putEvent()
    
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'MA组合演示策略初始化')
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
                
        
        """收到Bar推送（必须由用户继承实现）"""
        am = self.am        
        am.updateBar(bar)
        
        #if not am.inited:
            #return
        
        # 计算快慢均线
        fastMa = am.ma(self.fastWindow, array=True)
       
        self.fastMa0 = fastMa[-1]
        self.fastMa1 = fastMa[-2]
        
        slowMa = am.ma(self.slowWindow, array=True)
        self.slowMa0 = slowMa[-1]
        self.slowMa1 = slowMa[-2]
        
        #计算中速均线 
        self.md1MA0 =am.ma(self.md1Window)     
        self.md2MA0 = am.ma(self.md2Window)
        
        #计算偏移值
        self.offsetValue,close,high,low=am.offset(self.offsetWindow)

        # 判断买卖
        crossOver = self.fastMa0>self.slowMa0 and self.fastMa1<self.slowMa1 and\
           self.md1MA0>self.md2MA0 and self.offsetValue< (1-self.threshold)# 金叉上穿
        
        crossBelow = self.fastMa0<self.slowMa0 and self.fastMa1>self.slowMa1 and\
            self.md1MA0 < self.md2MA0 and self.offsetValue > self.threshold # 死叉下穿
        
        # 金叉和死叉的条件是互斥
        # 所有的委托均以K线收盘价委托（这里有一个实盘中无法成交的风险，考虑添加对模拟市价单类型的支持）

        if crossOver:
            print self.offsetValue,close,high,low,bar.date
            # 如果金叉时手头没有持仓，则直接做多
            if self.pos == 0:
                self.buy(bar.close, self.fixedSize)
           
                print '做多：',self.fixedSize
            # 如果有空头持仓，则先平空，再做多
            elif self.pos < 0:
                self.cover(bar.close, abs(self.pos))
                self.buy(bar.close, self.fixedSize)

                print '平仓/做多：',abs(self.pos),self.fixedSize
            #如果金叉时手头还有持仓，则加多
            elif self.pos > 0:
                self.buy(bar.close, self.fixedSize)

                print '加多：',self.fixedSize
        # 死叉和金叉相反
        elif crossBelow:
            print self.offsetValue,close,high,low,bar.date
            if self.pos == 0:
                self.short(bar.close, self.fixedSize)

                print '做空：',self.fixedSize
            elif self.pos > 0:
                self.sell(bar.close, abs(self.pos))
                self.short(bar.close, self.fixedSize)

                print '平仓/做空：',abs(self.pos),self.fixedSize
             #如果死叉时手头还有持仓，则加空
            elif self.pos < 0:
                self.short(bar.close, self.fixedSize)

                print '加空：',self.fixedSize
                
                
        # 同步数据到数据库
        self.saveSyncData()

        # 发出状态更新事件
        self.putEvent()
        
    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
    
    #----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        if self.pos!=0:
            if trade.direction =='多':
                print
            elif trade.direction =='空':
                pass
            else；
                pass
            #print trade.symbol,trade.price,trade.volume,trade.direction
        
    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass    
