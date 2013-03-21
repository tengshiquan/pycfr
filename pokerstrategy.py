from pokertrees import *

class Strategy(object):
    def __init__(self, player):
        self.player = player
        self.policy = {}

    def build_default(self, gametree):
        for key in gametree.information_sets:
            node = gametree.information_sets[key][0]
            if node.player == self.player:
                prob = 1.0 / float(len(node.children))
                probs = [0,0,0]
                for action in range(3):
                    if node.valid(action):
                        probs[action] = prob
                self.policy[node.player_view] = probs

    def probs(self, infoset):
        assert(infoset in self.policy)
        return self.policy[infoset]

    def load_from_file(self, filename):
        self.policy = {}
        f = open(filename, 'r')
        for line in f:
            line = line.strip()
            if line == "" or line.startswith('#'):
                continue
            tokens = line.split(' ')
            assert(len(tokens) == 4)
            key = tokens[0]
            probs = [float(x) for x in reversed(tokens[1:])]
            self.policy[key] = probs

    def save_to_file(self, filename):
        f = open(filename, 'w')
        for key in sorted(self.policy.keys()):
            val = self.policy[key]
            f.write("{0} {1:.9f} {2:.9f} {3:.9f}\n".format(key, val[2], val[1], val[0]))
        f.flush()
        f.close()

class StrategyProfile(object):
    def __init__(self, gametree, strategies):
        assert(gametree.players == len(strategies))
        self.gametree = gametree
        self.strategies = strategies

    def expected_value(self):
        return self.ev_helper(self.gametree.root, 1)

    def ev_helper(self, root, pathprob, depth = 0):
        if type(root) is TerminalNode:
            payoffs = [x*pathprob for x in root.payoffs]
            #print '{0}Probpath: {1:.9f} Raw Payoffs: {2} Weighted: {3}'.format('\t'*depth, pathprob, root.payoffs, [float("{0:.4f}".format(x)) for x in payoffs])
            return payoffs
        if type(root) is HolecardChanceNode or type(root) is BoardcardChanceNode:
            payoffs = [0] * self.gametree.players
            prob = pathprob / float(len(root.children))
            #print '{0}Probpath: {1:.9f} Holes: {2} Board: {3} Children: {4}'.format('\t'*depth, pathprob, root.holecards, root.board, len(root.children))
            for child in root.children:
                subpayoffs = self.ev_helper(child, prob, depth+1)
                for i,p in enumerate(subpayoffs):
                    payoffs[i] += p
            return payoffs
        # Otherwise, it's an ActionNode
        probs = self.strategies[root.player].probs(root.player_view)
        #print '{0}Probpath: {1:.9f} PlayerView: {2} ActionProbs: {3}'.format('\t'*depth, pathprob, root.player_view, probs)
        payoffs = [0] * self.gametree.players
        if root.fold_action and probs[FOLD] > 0.0000000001:
            subpayoffs = self.ev_helper(root.fold_action, pathprob * probs[FOLD], depth+1)
            for i,p in enumerate(subpayoffs):
                payoffs[i] += p
        if root.call_action and probs[CALL] > 0.0000000001:
            subpayoffs = self.ev_helper(root.call_action, pathprob * probs[CALL], depth+1)
            for i,p in enumerate(subpayoffs):
                payoffs[i] += p
        if root.raise_action and probs[RAISE] > 0.0000000001:
            subpayoffs = self.ev_helper(root.raise_action, pathprob * probs[RAISE], depth+1)
            for i,p in enumerate(subpayoffs):
                payoffs[i] += p
        return payoffs

