import logging
from typing import Dict

from core.models.models import Signal
class PerformanceTracker:
    """Rastreador de rendimiento de señales"""
    
    def __init__(self):
        self.trades = []
        self.logger = logging.getLogger(__name__)
    
    def record_trade(self, signal: Signal, result: str, profit_loss: float):
        """Registra resultado de trade"""
        trade_record = {
            'timestamp': signal.timestamp.isoformat(),
            'signal_type': signal.signal_type.value,
            'entry_price': signal.entry_price,
            'confidence': signal.confidence,
            'result': result,  # 'win', 'loss'
            'profit_loss': profit_loss,
            'reason': signal.reason
        }
        
        self.trades.append(trade_record)
        self.logger.info(f"Trade registrado: {result} | P&L: {profit_loss}")
    
    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de rendimiento"""
        if not self.trades:
            return {}
        
        wins = [t for t in self.trades if t['result'] == 'win']
        losses = [t for t in self.trades if t['result'] == 'loss']
        
        win_rate = len(wins) / len(self.trades) * 100
        total_pnl = sum(t['profit_loss'] for t in self.trades)
        avg_win = sum(t['profit_loss'] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t['profit_loss'] for t in losses) / len(losses) if losses else 0
        
        return {
            'total_trades': len(self.trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': round(win_rate, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(abs(avg_win / avg_loss) if avg_loss != 0 else 0, 2)
        }