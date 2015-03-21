var syscat = angular.module('syscat',['ngRoute'])
syscat.config([ '$routeProvider', function($routeProvider){
	$routeProvider.when('/busqueda',{
		templateUrl: 'static/templates/busqueda.html'
	}).otherwise({
		redirectTo: '/',
		templateUrl: 'index.html'
	})
}])