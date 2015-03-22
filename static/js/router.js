var sys = angular.module('syscat',['ngRoute'])
sys.config([ '$routeProvider', 
	function($routeProvider){
		$routeProvider
		.when('/busqueda',
			{
				templateUrl: 'static/templates/busqueda.html'
			})
		.when('/index.html',
			{
				redirectTo: '/'
			})
		.otherwise({
			redirectTo: '/'
		})
	}])