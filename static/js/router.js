var sys = angular.module('syscat', ['ngRoute']);
sys.config([ '$routeProvider', 
	function ($routeProvider) {
		$routeProvider
		.when('/busqueda',
			{
				templateUrl: 'static/templates/busqueda.html'
			})
		.when('/registro',
			{
				templateUrl: 'static/templates/registro.html'
			})
		.otherwise({
			redirectTo: '/'
		});
        $locationProvider.html5Mode(true);
	}]);