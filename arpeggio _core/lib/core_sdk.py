class Splitting:

    def __init__(self, net_target:int):

        # set the projection for the base coins
        self.net_target = net_target #i.e $105000

    def cumpute_moneys_owed(self, amount_in_tokens_required:float, neglect_ratio:float):

        #find the 1:1 share
        real_share = self.calc_real_share(amount_in_tokens_required)

        #determine the last known splitting parameters
        #define by how much the previous visited wallet has been neglected
        nr = neglect_ratio #i.e ,99%

        #make the final dollar amount
        amount = real_share - real_share * nr
        return amount

    # this method assumes a 1:1 scale for amount and share
    # inputs a dollar amount
    def calc_real_share(self, amount_in_tokens:float):
        
        real_share = self.net_target * amount_in_tokens
        return real_share
    
    # sum of these value found using the last_block_added attribute @bc
    def calc_neglect_ratio(self, tokens_received:float, amount_paid:float):
        
        # determine the 1:1 share
        rs = amount_paid/self._net_target

        #return a percentile of 100
        return 1-tokens_received/rs

    def sum_neglect_ratios(self, total_mint:int
                           , new_mint
                           , original_ratio:float
                           , new_ratio: float):

        #solve for zero division
        total_mint += 1 if not total_mint else 0
        
        #find the ratio of this mint to the total_mint thus far
        r = new_mint/total_minted

        #each minted share amount minted will weight different
        return original_ratio + (min([r,new_ratio])/max([r,new_ratio]))
        
        
