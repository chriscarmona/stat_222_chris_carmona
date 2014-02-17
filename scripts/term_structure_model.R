##################################################
interpolation <- function( x, fx, x_new, method=c("linear","exp","log","spline")[1] ) {
  # Given a set of points (x,fx), this function obtain the interpolated values of x_new
  
  x_new_bucket <- rep(1,length(x_new))
  for( i in seq(x) ) {
    x_new_bucket <- ifelse(x_new>x[i], i+1, x_new_bucket)
  }
  x_new_bucket <- ifelse(x_new==x[1], 2, x_new_bucket)
  temp <- !is.element(x_new_bucket,c(1,length(x)+1))
  fx_new <- as.numeric(NULL)
  if(method=="linear") {
    # Smoothing via "Linear interpolation"
    w <- rep(NA,length(x_new))
    w[temp] <- (x[x_new_bucket[temp]]-x_new[temp]) / (x[x_new_bucket[temp]] - x[x_new_bucket[temp]-1])
    fx_new <- rep(NA,length(x_new))
    fx_new[temp] <- fx[x_new_bucket[temp]-1] * w[temp] + fx[x_new_bucket[temp]] * (1-w[temp])
  }
  if(method=="exp") {
    # Smoothing via "exponential interpolation"
    w <- rep(NA,length(x_new))
    w[temp] <- (x[x_new_bucket[temp]]-x_new[temp]) / (x[x_new_bucket[temp]] - x[x_new_bucket[temp]-1])
    fx_new[temp] <- log( exp(fx[x_new_bucket[temp]-1]) * w[temp] + exp(fx[x_new_bucket[temp]]) * (1-w[temp]) )
  }
  if(method=="log") {
    # Smoothing via "Logarithmic interpolation"
    w <- rep(NA,length(x_new))
    w[temp] <- (x[x_new_bucket[temp]]-x_new[temp]) / (x[x_new_bucket[temp]] - x[x_new_bucket[temp]-1])
    #fx_new[temp] <- exp( log(fx[x_new_bucket[temp]-1]) * w[temp] + log(fx[x_new_bucket[temp]]) * (1-w[temp]) )
    fx_new[temp] <- fx[x_new_bucket[temp]-1]^w[temp] * fx[x_new_bucket[temp]]^(1-w[temp])
  }
  if(method=="spline") {
    # Smoothing via "Smoothing spline"
    smooth_model <- smooth.spline(cbind(x,fx))
    fx_new <- predict(smooth_model,x_new)$y
  }
  return(fx_new)
}

##################################################

##################################################

zero_from_yield_bootstrap <- function ( nodes, ytm_curve, smooth=c("linear","exp","log","spline")[2] ) {
  # Function to calculate zero-coupon rates, z_t, using bootstrapping
  # using data acording to market quotes, y_t
  #   for t > 1 year: anualized yield to maturity for bonds paying semiannual coupons
  #   fot t <=1 year: adjusted discount rate, i.e. ((100-P)/P)*(365/days to maturity)
  # the output rate will be annual and continuosly compounded
  
  # Input:
  #   ytm_curve: a numeric vector with yields in the market standard
  #   nodes: a numeric  vector with the terms of ytm_curve in years
  # Output
  #   zero_curve_boot :a numeric vector with the corresponding zero-coupon yields
  
  ytm_curve <- as.numeric(ytm_curve)
  
  nodes_t <- as.numeric(substr( nodes , 1, nchar(nodes)-1 ))
  nodes_t[substr( nodes , nchar(nodes), nchar(nodes) )=="m"] <- nodes_t[substr( nodes , nchar(nodes), nchar(nodes) )=="m"]/12
  if(!all(nodes_t==sort(nodes_t,decreasing=F))) {
    stop("Introduced values have to be increasing with respect to 'nodes'")
  }
  
  # Get rid of NA's
  nodes_orig_t <- nodes_t
  nodes <- nodes[!is.na(ytm_curve)]
  nodes_t <- nodes_t[!is.na(ytm_curve)]
  ytm_curve <- ytm_curve[!is.na(ytm_curve)]
  
  # Validates that the vector has first, last and one additional node.
  if(
    !( all( is.element( nodes_orig_t[c(1,length(nodes_orig_t))] , nodes_t[c(1,length(nodes_t))] ) ) & length(nodes)>3 )
  ) { return( rep(NA,length(nodes_orig_t)) ) }
  
  # Interpolation of values in the input yields for terms that are not specified but needed in the algorithm
  ytm_pred_t <- sort(unique( c( nodes_t, seq(0.5,max(nodes_t),0.5) ) ))
  ytm_pred <- interpolation(x=nodes_t,fx=ytm_curve,x_new=ytm_pred_t,method=smooth)

  # Validates that the interpolations does not give negative values
  if(any(ytm_pred<0)) { stop("The interpolation method is calculating negatives yields") }
  
  # Zero-coupon yield calculation via bootstrappping
  # Assumptions:
  # 1) Quotation according to market stndards:
  #   1.1) for t<=1 instruments are zero-coupon bonds
  zero_curve_boot <- ytm_pred
  zero_curve_boot[ytm_pred_t<=1] <- ( 1 + ytm_pred[ytm_pred_t<=1] * ytm_pred_t[ytm_pred_t<=1] ) ^ (1/ytm_pred_t[ytm_pred_t<=1])-1
  zero_curve_boot[ytm_pred_t>1] <- NA
  #   validation
  if( any(round( ( (1+ytm_pred[ytm_pred_t<=1]*ytm_pred_t[ytm_pred_t<=1])^(-1) ) - ( (1+zero_curve_boot[ytm_pred_t<=1])^(-ytm_pred_t[ytm_pred_t<=1]) ) , 12 ) >0) ) {
    stop("Zero-coupon rates were not calculated correctly for terms t<=1")
  }
  
  #   1.2) for t>1 instruments are coupon bonds, with payments at: 0.5, 1, 1.5, 2, 2.5,...
  # ytm are nominales semi-anually compounded
  node_coupon <- is.element(ytm_pred_t,seq(0.5,max(ytm_pred_t),0.5))
  
  for( node_i in ytm_pred_t[ytm_pred_t>1] ) {
    
    ytm_i <- ytm_pred[match(node_i,ytm_pred_t)]
    
    # cupon rate that makes bond price=100
    cpn_i <- ytm_i/2
    
    # zero-rate for node_i
    zero_curve_boot[match(node_i,ytm_pred_t)] <-    
      ( ( 1-cpn_i*sum( ( 1 + zero_curve_boot[node_coupon & (ytm_pred_t<node_i)] )^(-ytm_pred_t[node_coupon & (ytm_pred_t<node_i)]) ) ) / ( 1+cpn_i ) )^(-1/node_i) - 1
    
    # Validation
    if( 100 != round( sum(100*cpn_i*(1+zero_curve_boot[node_coupon & (ytm_pred_t<=node_i)])^( -ytm_pred_t[node_coupon & (ytm_pred_t<=node_i)] ) ) + 100*(1+zero_curve_boot[ytm_pred_t==node_i])^-ytm_pred_t[ytm_pred_t==node_i] ,12) ) {
      stop("Zero-coupon rates were not calculated correctly for terms t>1")
    }
    #plot(zero_curve_boot,pch=20,col=2)
    #points(ytm_pred,pch=20,col=4)
    #legend("top",c("zero","ytm"),col=c(2,4),pch=19)
    
  }
  
  return( zero_curve_boot[match(nodes_orig_t,ytm_pred_t)] )
}

##################################################