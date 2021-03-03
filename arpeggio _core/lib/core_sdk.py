class Splitting:

    def __init__(self, netx_target:int):

        # set the projection for the base coins
        self.netx_target = netx_target #i.e $105000

    def split(self, amount:float, neglect_ratio:float, netx_fee:float):
        
        #find the 1:1 share
        rs = self.calc_real_share(amount)
        
        #determine the last known splitting parameters
        #1.by how much the previous visited wallet has been neglected
        nr = neglect_ratio #i.e ,99%

        #make the split
        split = rs - rs * nr

        return split

    # this method assumes a 1:1 scale for amount and share
    def calc_real_share(self, amount:float):
        
        real_share = self.netx_target(amount/self.netx_target)
        return real_share
    
    # sum of these value found using the last_block_added attribute @bc
    # calls this method at publishing blocks as well
    def calc_neglect_ration(self, amount_paid:float, share_received:float):
        
        # determine the 1:1 share
        rs = self.calc_real_share(amount_paid)
        
        # determine the neglect ration
        nr = 1-share_received/rs
        
        return nr

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
        
        
